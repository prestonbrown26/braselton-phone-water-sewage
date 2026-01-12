"""Django views for Braselton AI Phone Agent."""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timezone, timedelta
import uuid
from typing import Iterable

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import QuerySet
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail

from .email_templates import DEFAULT_EMAIL_TEMPLATES, ensure_all_email_templates, ensure_email_template
from .email_utils import send_billing_email
from .models import (
    CallLog,
    EmailEvent,
    EmailTemplateConfig,
    PhoneConfiguration,
    TransferEvent,
    InviteToken,
    PasswordResetToken,
)
from .utils import format_eastern, verify_webhook_secret

logger = logging.getLogger(__name__)
User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def annotate_call_logs(logs: Iterable[CallLog]) -> None:
    for log in logs:
        log.display_time = format_eastern(log.created_at)
        email_events = getattr(log, "email_events", None)
        if email_events:
            for event in email_events.all():
                event.display_time = format_eastern(event.created_at)
                event.template_label = (event.template_type or "").replace("_", " ").title()
        transfer_events = getattr(log, "transfer_events", None)
        if transfer_events:
            for event in transfer_events.all():
                event.display_time = format_eastern(event.created_at)


def get_email_template(email_type: str) -> tuple[str, str]:
    template = EmailTemplateConfig.objects.filter(template_type=email_type).first()
    if not template:
        template = ensure_email_template(email_type)
    return template.subject, template.body


def _parse_json_body(request: HttpRequest) -> dict:
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# Public views
# ---------------------------------------------------------------------------
def home(request: HttpRequest) -> HttpResponse:
    """Default landing: send unauthenticated users to login, admins to dashboard."""

    if request.user.is_authenticated:
        return redirect("admin-dashboard")
    return redirect("admin-login")


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------
@csrf_exempt
def webhook_email(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)
    if not verify_webhook_secret(request):
        return JsonResponse({"error": "unauthorized"}, status=401)

    data = _parse_json_body(request)
    logger.info("Received email webhook data: %s", data)

    args = data.get("args", data) or {}
    email_type = args.get("email_type", "payment_link")
    user_email = args.get("user_email")
    call_id = args.get("call_id") or (data.get("call") or {}).get("call_id") or "unknown"
    caller_number = args.get("caller_phone") or (data.get("call") or {}).get("from_number")

    if not user_email:
        logger.error("Missing user_email in webhook data: %s", data)
        return JsonResponse({"error": "user_email is required"}, status=400)

    subject, body = get_email_template(email_type)
    send_billing_email(to_address=user_email, subject=subject, body=body)

    with transaction.atomic():
        call_log = (
            CallLog.objects.select_for_update()
            .filter(call_id=call_id)
            .first()
        )

        # Fallback: if call_id not found, try to attach to the most recent call from the same number.
        if not call_log and caller_number:
            recent_call = (
                CallLog.objects.select_for_update()
                .filter(caller_number=caller_number)
                .order_by("-created_at")
                .first()
            )
            if recent_call:
                call_log = recent_call
                call_id = call_log.call_id
                logger.info(
                    "Attached email webhook to existing call %s via caller_number match (%s)",
                    call_id,
                    caller_number,
                )

        if not call_log:
            placeholder_text = (
                "Call log placeholder created automatically because the email webhook "
                "arrived before the transcript webhook."
            )
            call_log = CallLog.objects.create(
                call_id=call_id,
                caller_number=caller_number,
                transcript=placeholder_text,
                sentiment="neutral",
                transferred=False,
                email_sent=False,
                created_at=datetime.now(timezone.utc),
            )
            logger.warning(
                "Created placeholder call log for %s because email arrived before transcript.",
                call_id,
            )

        call_log.email_sent = True
        call_log.save(update_fields=["email_sent"])

        EmailEvent.objects.create(
            call=call_log,
            template_type=email_type,
            recipient=user_email,
            subject=subject,
            body=body,
        )

    logger.info("Email sent for call %s to %s", call_id, user_email)
    return JsonResponse({"status": "sent", "email_type": email_type})


@csrf_exempt
def webhook_transcript(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)
    if not verify_webhook_secret(request):
        return JsonResponse({"error": "unauthorized"}, status=401)

    payload = _parse_json_body(request)
    logger.info("Received transcript webhook payload: %s", payload)

    event_type = payload.get("event")
    if event_type != "call_ended":
        logger.info("Ignoring unsupported event '%s'", event_type)
        return JsonResponse({"status": "ignored", "event": event_type})

    call_data = payload.get("call", {}) or {}
    call_id = call_data.get("call_id")
    if not call_id:
        return JsonResponse({"error": "call.call_id is required"}, status=400)

    caller_number = call_data.get("from_number")
    start_ts = call_data.get("start_timestamp")
    end_ts = call_data.get("end_timestamp")
    duration_seconds: int | None = None
    call_end_dt = None

    if isinstance(start_ts, (int, float)) and isinstance(end_ts, (int, float)):
        duration_seconds = max(0, int((end_ts - start_ts) / 1000))

    if isinstance(end_ts, (int, float)):
        call_end_dt = datetime.fromtimestamp(end_ts / 1000, tz=timezone.utc)
    else:
        call_end_dt = datetime.now(timezone.utc)

    transcript = (call_data.get("transcript") or "").strip()
    if not transcript:
        stitched_lines: list[str] = []
        for entry in call_data.get("transcript_with_tool_calls") or []:
            role = entry.get("role")
            content = (entry.get("content") or "").strip()
            if role and content:
                stitched_lines.append(f"{role.capitalize()}: {content}")
        if stitched_lines:
            transcript = "\n".join(stitched_lines)

    if not transcript:
        recording_url = call_data.get("recording_url") or call_data.get("public_log_url")
        transcript = "Transcript not provided by Retell. "
        if recording_url:
            transcript += f"Reference recording: {recording_url}"
        else:
            transcript += "No recording URL supplied."

    with transaction.atomic():
        existing = (
            CallLog.objects.select_for_update()
            .filter(call_id=call_id)
            .first()
        )
        if existing:
            # Update placeholder/partial record with the real transcript/metadata.
            existing.transcript = transcript or existing.transcript
            if caller_number:
                existing.caller_number = caller_number
            if duration_seconds is not None:
                existing.duration_seconds = duration_seconds
            if call_end_dt:
                existing.created_at = call_end_dt
            existing.sentiment = existing.sentiment or "neutral"
            existing.save(
                update_fields=[
                    "transcript",
                    "caller_number",
                    "duration_seconds",
                    "created_at",
                    "sentiment",
                ]
            )
            logger.info("Call %s updated with transcript/metadata; acking webhook", call_id)
            return JsonResponse({"status": "updated"})

        # Attempt to reconcile with a recent placeholder created by the email webhook
        placeholder = (
            CallLog.objects.select_for_update()
            .filter(
                caller_number=caller_number,
                email_sent=True,
                transcript__startswith="Call log placeholder",
            )
            .order_by("-created_at")
            .first()
        )

        new_call = CallLog.objects.create(
            call_id=call_id,
            caller_number=caller_number,
            transcript=transcript,
            duration_seconds=duration_seconds,
            sentiment="neutral",
            transferred=False,
            email_sent=False,
            created_at=call_end_dt,
        )

        # If there was a placeholder for this caller, migrate its email events and delete it.
        if placeholder:
            moved = EmailEvent.objects.filter(call=placeholder).update(call=new_call)
            if moved:
                new_call.email_sent = True
                new_call.save(update_fields=["email_sent"])
            placeholder.delete()
            logger.info(
                "Merged placeholder call %s into %s (moved %s email events)",
                placeholder.call_id,
                call_id,
                moved,
            )

    logger.info("Stored call %s (duration=%s sec, caller=%s)", call_id, duration_seconds, caller_number)
    return JsonResponse({"status": "ok"})


@csrf_exempt
def webhook_transfer(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)
    if not verify_webhook_secret(request):
        return JsonResponse({"error": "unauthorized"}, status=401)

    data = _parse_json_body(request)
    logger.info("Received transfer webhook payload: %s", data)

    call_id = data.get("call_id")
    if not call_id:
        return JsonResponse({"error": "call_id is required"}, status=400)

    target_number = data.get("target_number")
    reason = data.get("reason")
    notes = data.get("notes") or data.get("details")

    with transaction.atomic():
        call_log = CallLog.objects.select_for_update().filter(call_id=call_id).first()
        if not call_log:
            placeholder_text = "Transfer webhook received before transcript; placeholder created."
            call_log = CallLog.objects.create(
                call_id=call_id,
                caller_number=data.get("from_number"),
                transcript=placeholder_text,
                sentiment="neutral",
                transferred=False,
                email_sent=False,
                created_at=datetime.now(timezone.utc),
            )

        TransferEvent.objects.create(
            call=call_log,
            target_number=target_number,
            reason=reason,
            notes=notes,
        )
        CallLog.objects.filter(call_id=call_id).update(transferred=True)

    logger.info("Logged transfer for call %s → %s", call_id, target_number or "unknown target")
    return JsonResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------
def admin_login(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("admin-dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get("next") or reverse("admin-dashboard")
            return redirect(next_url)

        messages.error(request, "Invalid username or password")

    return render(request, "login.html")


@login_required
def admin_logout(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("admin-login")


def forgot_password(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        if not email:
            messages.error(request, "Email is required.")
            return redirect("forgot-password")
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            messages.error(request, "If that email exists, a reset link will be sent.")
            return redirect("forgot-password")
        token = uuid.uuid4().hex
        expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
        PasswordResetToken.objects.create(user=user, token=token, expires_at=expires_at)
        reset_link = request.build_absolute_uri(reverse("reset-password") + f"?token={token}")
        send_mail(
            subject="Reset your Braselton Water/Sewer admin password",
            message=f"Click to reset your password: {reset_link}\n\nThis link expires in 2 hours.",
            from_email=getattr(settings, "EMAIL_FROM_ADDRESS", None),
            recipient_list=[email],
            fail_silently=False,
        )
        messages.success(request, "If that email exists, a reset link has been sent.")
        return redirect("forgot-password")
    return render(request, "forgot_password.html")


def reset_password(request: HttpRequest) -> HttpResponse:
    token_val = request.GET.get("token") or request.POST.get("token")
    if not token_val:
        return render(request, "password_reset.html", {"error": "Missing token"}, status=400)
    token = PasswordResetToken.objects.filter(token=token_val, used=False).first()
    if not token or token.expires_at < datetime.now(timezone.utc):
        return render(request, "password_reset.html", {"error": "Token is invalid or expired"}, status=400)
    if request.method == "POST":
        password = (request.POST.get("password") or "").strip()
        if not password:
            return render(request, "password_reset.html", {"error": "Password is required", "token": token_val}, status=400)
        user = token.user
        user.set_password(password)
        user.save()
        token.used = True
        token.save(update_fields=["used"])
        messages.success(request, "Password reset. Please sign in.")
        return redirect("admin-login")
    return render(request, "password_reset.html", {"token": token_val})


def accept_invite(request: HttpRequest) -> HttpResponse:
    token_val = request.GET.get("token") or request.POST.get("token")
    if not token_val:
        return render(request, "accept_invite.html", {"error": "Missing token"}, status=400)
    invite = InviteToken.objects.filter(token=token_val, used=False).first()
    if not invite or invite.expires_at < datetime.now(timezone.utc):
        return render(request, "accept_invite.html", {"error": "Invite is invalid or expired"}, status=400)
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()
        if not username or not password:
            return render(request, "accept_invite.html", {"error": "Username and password are required", "token": token_val}, status=400)
        if User.objects.filter(username=username).exists():
            return render(request, "accept_invite.html", {"error": "Username already taken", "token": token_val}, status=400)
        user = User.objects.create_user(
            username=username,
            password=password,
            email=invite.email,
            is_staff=invite.is_staff,
            is_superuser=invite.is_superuser,
            is_active=True,
        )
        invite.used = True
        invite.save(update_fields=["used"])
        messages.success(request, "Account created. Please sign in.")
        return redirect("admin-login")
    return render(request, "accept_invite.html", {"token": token_val, "email": invite.email})


# ---------------------------------------------------------------------------
# Admin views
# ---------------------------------------------------------------------------
@login_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    if request.method == "POST" and request.POST.get("ticket_form"):
        title = (request.POST.get("ticket_title") or "").strip()
        ticket_type = (request.POST.get("ticket_type") or "feature").strip()
        description = (request.POST.get("ticket_description") or "").strip()
        recipient = None
        phone_config = PhoneConfiguration.objects.first()
        if phone_config and phone_config.transfer_request_email:
            recipient = phone_config.transfer_request_email
        if not recipient:
            recipient = getattr(settings, "EMAIL_FROM_ADDRESS", None)
        if not recipient:
            messages.error(request, "Ticket could not be sent: no recipient configured.")
        else:
            user_email = request.user.email if request.user.is_authenticated else "n/a"
            body = (
                f"New ticket submitted by {request.user.username} (email: {user_email})\n"
                f"Type: {ticket_type}\n"
                f"Title: {title or 'No title'}\n\n"
                f"Description:\n{description}"
            )
            send_mail(
                subject=f"[Ticket] {ticket_type.capitalize()}: {title or 'No title'}",
                message=body,
                from_email=getattr(settings, "EMAIL_FROM_ADDRESS", None),
                recipient_list=[recipient],
                fail_silently=False,
            )
            messages.success(request, "Ticket submitted. Thank you for the feedback.")
        return redirect("admin-dashboard")

    total_calls = CallLog.objects.count()
    latest_call = CallLog.objects.first()
    total_emails = EmailEvent.objects.count()
    total_transfers = TransferEvent.objects.count()
    phone_config = PhoneConfiguration.objects.first()
    recent_calls = (
        CallLog.objects.all()
        .prefetch_related("email_events", "transfer_events")
        .order_by("-created_at")[:5]
    )
    annotate_call_logs(recent_calls)

    return render(
        request,
        "admin_home.html",
        {
            "stats": {
                "total_calls": total_calls,
                "total_emails": total_emails,
                "total_transfers": total_transfers,
                "last_call_time": format_eastern(latest_call.created_at) if latest_call else "—",
            },
            "recent_calls": recent_calls,
            "phone_config": phone_config,
            "active_page": "home",
        },
    )


@login_required
def admin_calls(request: HttpRequest) -> HttpResponse:
    page_number = request.GET.get("page", 1)
    qs = (
        CallLog.objects.all()
        .prefetch_related("email_events", "transfer_events")
        .order_by("-created_at")
    )
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(page_number)
    annotate_call_logs(page_obj.object_list)
    return render(
        request,
        "admin_calls.html",
        {"logs": page_obj, "page_obj": page_obj, "active_page": "calls"},
    )


@login_required
def admin_transcripts(request: HttpRequest) -> HttpResponse:
    call_id = request.GET.get("call_id") or ""
    phone = request.GET.get("phone") or ""
    date_str = request.GET.get("date") or ""

    query: QuerySet[CallLog] = CallLog.objects.all()

    if call_id:
        query = query.filter(call_id__icontains=call_id)
    if phone:
        query = query.filter(caller_number__icontains=phone)
    if date_str:
        try:
            search_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            query = query.filter(created_at__date=search_date)
        except ValueError:
            pass

    page_number = request.GET.get("page", 1)
    qs = query.prefetch_related("email_events", "transfer_events").order_by("-created_at")
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(page_number)
    annotate_call_logs(page_obj.object_list)

    return render(
        request,
        "admin_transcripts.html",
        {
            "results": page_obj,
            "page_obj": page_obj,
            "search_params": {
                "call_id": call_id,
                "phone": phone,
                "date": date_str,
            },
            "retention_days": settings.LOG_RETENTION_DAYS,
            "active_page": "transcripts",
        },
    )


@login_required
def admin_settings(request: HttpRequest) -> HttpResponse:
    # Handle Phone Configuration
    phone_config = PhoneConfiguration.objects.first()
    if not phone_config:
        phone_config = PhoneConfiguration.objects.create(
            retell_ai_phone_number=None,
            retell_ai_phone_label=None,
            transfer_phone_numbers=[],
            transfer_phone_book=[],
        )

    if request.method == "POST":
        if "phone_config_form" in request.POST:
            if not request.user.is_superuser:
                messages.error(request, "Only superusers can update phone configuration.")
                return redirect("admin-settings")
            retell_number = (request.POST.get("retell_ai_phone_number") or "").strip()
            retell_label = (request.POST.get("retell_ai_phone_label") or "").strip()
            req_email = (request.POST.get("transfer_request_email") or "").strip()
            labels = request.POST.getlist("transfer_label")
            numbers = request.POST.getlist("transfer_number")
            transfer_entries = []
            for label, number in zip(labels, numbers):
                number = (number or "").strip()
                label = (label or "").strip()
                if not number:
                    continue
                transfer_entries.append({"label": label or "Transfer", "number": number})
            transfer_numbers = [entry["number"] for entry in transfer_entries]

            phone_config.retell_ai_phone_number = retell_number or None
            phone_config.retell_ai_phone_label = retell_label or None
            phone_config.transfer_phone_numbers = transfer_numbers
            phone_config.transfer_phone_book = transfer_entries
            phone_config.transfer_request_email = req_email or None
            phone_config.save()
            messages.success(request, "Phone configuration saved.")
            return redirect("admin-settings")

        if "transfer_request" in request.POST:
            req_label = (request.POST.get("req_transfer_label") or "").strip()
            req_number = (request.POST.get("req_transfer_number") or "").strip()
            req_desc = (request.POST.get("req_transfer_description") or "").strip()
            if not req_number:
                messages.error(request, "Transfer number is required for a request.")
                return redirect("admin-settings")
            body = (
                f"Transfer number change requested by {request.user.username} (email: {request.user.email or 'n/a'}).\n\n"
                f"Label: {req_label or 'n/a'}\n"
                f"Number: {req_number}\n"
                f"Description: {req_desc or 'n/a'}\n"
            )
            recipient = phone_config.transfer_request_email or getattr(
                settings, "EMAIL_FROM_ADDRESS", None
            )
            if not recipient:
                messages.error(request, "Request email recipient is not configured.")
            else:
                send_mail(
                    subject="Transfer number change request",
                    message=body,
                    from_email=getattr(settings, "EMAIL_FROM_ADDRESS", None),
                    recipient_list=[recipient],
                    fail_silently=False,
                )
                messages.success(request, "Request sent for transfer number change.")
            return redirect("admin-settings")

        if "user_form" in request.POST:
            if not request.user.is_superuser:
                messages.error(request, "Only superusers can create or edit users.")
                return redirect("admin-settings")
            username = (request.POST.get("username") or "").strip()
            email = (request.POST.get("email") or "").strip()
            password = (request.POST.get("password") or "").strip()

            if not username or not password or not email:
                messages.error(request, "Username, email, and password are required.")
                return redirect("admin-settings")

            user, created = User.objects.get_or_create(username=username)
            user.email = email
            user.set_password(password)
            user.is_active = True
            user.save()

            if created:
                messages.success(request, f"User '{username}' created.")
            else:
                messages.success(request, f"Password updated for '{username}'.")

            return redirect("admin-settings")

        if "user_delete_id" in request.POST:
            if not request.user.is_superuser:
                messages.error(request, "Only superusers can delete users.")
                return redirect("admin-settings")
            user_id = request.POST.get("user_delete_id")
            try:
                target = User.objects.get(id=user_id)
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect("admin-settings")
            if target == request.user:
                messages.error(request, "You cannot delete your own account.")
                return redirect("admin-settings")
            target.delete()
            messages.success(request, f"User '{target.username}' deleted.")
            return redirect("admin-settings")

        if "invite_email" in request.POST:
            invite_email = (request.POST.get("invite_email") or "").strip()
            if not invite_email:
                messages.error(request, "Email is required.")
                return redirect("admin-settings")
            token = uuid.uuid4().hex
            expires_at = datetime.now(timezone.utc) + timedelta(days=2)
            InviteToken.objects.create(
                email=invite_email,
                token=token,
                invited_by=request.user,
                is_staff=True,
                is_superuser=False,
                expires_at=expires_at,
            )
            invite_link = request.build_absolute_uri(reverse("accept-invite") + f"?token={token}")
            send_mail(
                subject="You're invited to Braselton Water/Sewer Admin",
                message=f"You have been invited to create an account for the Braselton Water/Sewer AI Agent Dashboard.\n\nClick to accept: {invite_link}\n\nThis link expires in 48 hours.",
                from_email=getattr(settings, "EMAIL_FROM_ADDRESS", None),
                recipient_list=[invite_email],
                fail_silently=False,
            )
            messages.success(request, f"Invite sent to {invite_email}")
            return redirect("admin-settings")

    users = User.objects.all().order_by("-date_joined")
    for u in users:
        u.display_joined = format_eastern(u.date_joined)
    # Prefer the structured book; fall back to legacy list for display
    transfer_entries = phone_config.transfer_phone_book or [
        {"label": "", "number": n} for n in (phone_config.transfer_phone_numbers or [])
    ]
    return render(
        request,
        "admin_settings.html",
        {
            "config": phone_config,
            "transfer_entries": transfer_entries,
            "users": users,
            "can_manage_users": request.user.is_superuser,
            "can_manage_phone": request.user.is_superuser,
            "active_page": "admin-settings",
        },
    )


@login_required
def admin_export(request: HttpRequest) -> HttpResponse:
    def row_iter():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "id",
                "call_id",
                "caller_number",
                "transcript",
                "duration_seconds",
                "sentiment",
                "transferred",
                "email_sent",
                "created_at",
            ]
        )
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        for log in CallLog.objects.all().order_by("-created_at").iterator():
            writer.writerow(
                [
                    log.id,
                    log.call_id,
                    log.caller_number,
                    log.transcript,
                    log.duration_seconds,
                    log.sentiment,
                    log.transferred,
                    log.email_sent,
                    log.created_at.isoformat(),
                ]
            )
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    response = StreamingHttpResponse(row_iter(), content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=braselton_call_logs.csv"
    return response


@login_required
def manage_email_templates(request: HttpRequest) -> HttpResponse:
    ensure_all_email_templates()
    templates = {
        tpl.template_type: tpl
        for tpl in EmailTemplateConfig.objects.order_by("template_type").all()
    }
    template_list = [(key, templates.get(key)) for key in DEFAULT_EMAIL_TEMPLATES]

    if request.method == "POST":
        updated = False
        for template_type in DEFAULT_EMAIL_TEMPLATES:
            subject = (request.POST.get(f"{template_type}_subject") or "").strip()
            body = (request.POST.get(f"{template_type}_body") or "").strip()

            tpl = templates.get(template_type)
            if not tpl:
                continue

            defaults = DEFAULT_EMAIL_TEMPLATES[template_type]
            tpl.subject = subject or defaults["subject"]
            tpl.body = body or defaults["body"]
            tpl.save(update_fields=["subject", "body", "updated_at"])
            updated = True

        if updated:
            messages.success(request, "Email templates updated successfully.")
        else:
            messages.info(request, "No changes detected.")

        return redirect("admin-manage-email-templates")

    return render(
        request,
        "admin_email_templates.html",
        {
            "template_list": template_list,
            "template_keys": list(DEFAULT_EMAIL_TEMPLATES.keys()),
            "active_page": "templates",
        },
    )


@login_required
def call_detail(request: HttpRequest, log_id: int) -> HttpResponse:
    log = get_object_or_404(
        CallLog.objects.prefetch_related("email_events", "transfer_events"), pk=log_id
    )
    annotate_call_logs([log])
    return render(
        request,
        "admin_call_detail.html",
        {
            "log": log,
            "active_page": None,
        },
    )

