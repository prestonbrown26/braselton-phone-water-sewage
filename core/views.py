"""Django views for Braselton AI Phone Agent."""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Iterable

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .email_templates import DEFAULT_EMAIL_TEMPLATES, ensure_all_email_templates, ensure_email_template
from .email_utils import send_billing_email
from .models import CallLog, EmailEvent, EmailTemplateConfig, TransferEvent
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

    if not user_email:
        logger.error("Missing user_email in webhook data: %s", data)
        return JsonResponse({"error": "user_email is required"}, status=400)

    subject, body = get_email_template(email_type)
    send_billing_email(to_address=user_email, subject=subject, body=body)

    with transaction.atomic():
        call_log = CallLog.objects.filter(call_id=call_id).first()
        if not call_log:
            placeholder_text = (
                "Call log placeholder created automatically because the email webhook "
                "arrived before the transcript webhook."
            )
            call_log = CallLog.objects.create(
                call_id=call_id,
                caller_number=args.get("caller_phone"),
                transcript=placeholder_text,
                sentiment="neutral",
                transferred=False,
                email_sent=False,
                created_at=datetime.utcnow().replace(tzinfo=timezone.utc),
            )
            logger.warning("Created placeholder call log for %s because email arrived before transcript.", call_id)

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

    existing = CallLog.objects.filter(call_id=call_id).first()
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

    CallLog.objects.create(
        call_id=call_id,
        caller_number=caller_number,
        transcript=transcript,
        duration_seconds=duration_seconds,
        sentiment="neutral",
        transferred=False,
        email_sent=False,
        created_at=call_end_dt,
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
        call_log = CallLog.objects.filter(call_id=call_id).first()
        if not call_log:
            placeholder_text = "Transfer webhook received before transcript; placeholder created."
            call_log = CallLog.objects.create(
                call_id=call_id,
                caller_number=data.get("from_number"),
                transcript=placeholder_text,
                sentiment="neutral",
                transferred=False,
                email_sent=False,
                created_at=datetime.utcnow().replace(tzinfo=timezone.utc),
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


# ---------------------------------------------------------------------------
# Admin views
# ---------------------------------------------------------------------------
@login_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    total_calls = CallLog.objects.count()
    latest_call = CallLog.objects.first()
    total_emails = EmailEvent.objects.count()
    total_transfers = TransferEvent.objects.count()
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
            "active_page": "home",
        },
    )


@login_required
def admin_calls(request: HttpRequest) -> HttpResponse:
    logs = (
        CallLog.objects.all()
        .prefetch_related("email_events", "transfer_events")
        .order_by("-created_at")[:200]
    )
    annotate_call_logs(logs)
    return render(request, "admin_calls.html", {"logs": logs, "active_page": "calls"})


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

    results = (
        query.prefetch_related("email_events", "transfer_events")
        .order_by("-created_at")[:100]
    )
    annotate_call_logs(results)

    return render(
        request,
        "admin_transcripts.html",
        {
            "results": results,
            "search_params": {
                "call_id": call_id,
                "phone": phone,
                "date": date_str,
            },
            "active_page": "transcripts",
        },
    )


@login_required
def admin_export(request: HttpRequest) -> HttpResponse:
    output = io.StringIO()
    writer = csv.writer(output)
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

    for log in CallLog.objects.all().order_by("-created_at"):
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

    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type="text/csv",
    )
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
def manage_users(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect("admin-manage-users")

        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.is_active = True
        user.save()

        if created:
            messages.success(request, f"User '{username}' created.")
        else:
            messages.success(request, f"Password updated for '{username}'.")

        return redirect("admin-manage-users")

    users = User.objects.all().order_by("-date_joined")
    return render(
        request,
        "admin_users.html",
        {
            "users": users,
            "active_page": "users",
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

