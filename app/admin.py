"""Administrative routes for viewing call logs."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, Response, current_app, redirect, render_template, request, session, url_for, flash
from flask_login import login_required, login_user, logout_user, UserMixin

from . import db, login_manager
from .email_templates import DEFAULT_EMAIL_TEMPLATES, ensure_all_email_templates
from .models import CallLog, EmailEvent, EmailTemplateConfig, TransferEvent


admin_bp = Blueprint("admin", __name__)
EASTERN_TZ = ZoneInfo("America/New_York")


def _format_eastern(dt: datetime | None) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(EASTERN_TZ).strftime("%Y-%m-%d %I:%M %p ET")


def _annotate_call_log(log: CallLog) -> None:
    log.display_time = _format_eastern(log.created_at)
    for event in getattr(log, "email_events", []):
        event.display_time = _format_eastern(event.created_at)
    for event in getattr(log, "transfer_events", []):
        event.display_time = _format_eastern(event.created_at)


class AdminUser(UserMixin):
    """Simple user class for admin authentication."""
    
    def __init__(self, user_id):
        self.id = user_id


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login."""
    if user_id == "admin":
        return AdminUser(user_id)
    return None


@admin_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    """Admin login page."""
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        expected_user = current_app.config.get("ADMIN_USERNAME")
        expected_pass = current_app.config.get("ADMIN_PASSWORD")
        
        if username == expected_user and password == expected_pass:
            user = AdminUser("admin")
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin.dashboard"))
        else:
            flash("Invalid username or password", "error")
    
    return render_template("login.html")


@admin_bp.route("/admin/logout")
@login_required
def logout():
    """Logout admin user."""
    logout_user()
    return redirect(url_for("admin.login"))


@admin_bp.route("/admin/calls", methods=["GET"])
@login_required
def admin_calls():
    """Render recent call logs for the admin portal."""

    logs = CallLog.query.order_by(CallLog.created_at.desc()).limit(200).all()
    for log in logs:
        _annotate_call_log(log)
    return render_template("admin_calls.html", logs=logs, active_page="calls")


@admin_bp.route("/admin/transcripts", methods=["GET"])
@login_required
def search_transcripts():
    """Search for call transcripts by call ID, phone number, or date.
    
    Per Blake's requirement: "just need to put in call ID and get the transcript"
    """
    
    call_id = request.args.get("call_id")
    phone = request.args.get("phone")
    date = request.args.get("date")
    
    query = CallLog.query
    
    if call_id:
        query = query.filter(CallLog.call_id.contains(call_id))
    if phone:
        query = query.filter(CallLog.caller_number.contains(phone))
    if date:
        # Search by date (YYYY-MM-DD format)
        try:
            search_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(db.func.date(CallLog.created_at) == search_date)
        except ValueError:
            pass  # Invalid date format, ignore
    
    results = query.order_by(CallLog.created_at.desc()).limit(100).all()
    for log in results:
        _annotate_call_log(log)
    
    return render_template(
        "admin_transcripts.html",
        results=results,
        search_params={
            "call_id": call_id or "",
            "phone": phone or "",
            "date": date or "",
        },
        active_page="transcripts",
    )


@admin_bp.route("/admin/export", methods=["GET"])
@login_required
def export_calls():
    """Stream call logs as CSV for archival or compliance."""

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "call_id", "caller_number", "transcript", "duration_seconds",
        "sentiment", "transferred", "email_sent", "created_at"
    ])

    for log in CallLog.query.order_by(CallLog.created_at.desc()).all():
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
    return Response(
        output.read(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=braselton_call_logs.csv"},
    )


@admin_bp.route("/admin/email-templates", methods=["GET", "POST"])
@login_required
def manage_email_templates():
    """Allow admins to edit outbound email content."""

    ensure_all_email_templates()

    templates = {
        tpl.template_type: tpl
        for tpl in EmailTemplateConfig.query.order_by(EmailTemplateConfig.template_type).all()
    }

    if request.method == "POST":
        updated = False
        for template_type in DEFAULT_EMAIL_TEMPLATES:
            subject = request.form.get(f"{template_type}_subject", "").strip()
            body = request.form.get(f"{template_type}_body", "").strip()

            tpl = templates.get(template_type)
            if not tpl:
                continue

            defaults = DEFAULT_EMAIL_TEMPLATES[template_type]
            tpl.subject = subject or defaults["subject"]
            tpl.body = body or defaults["body"]
            updated = True

        if updated:
            db.session.commit()
            flash("Email templates updated successfully.", "success")
        else:
            flash("No changes detected.", "info")

        return redirect(url_for("admin.manage_email_templates"))

    return render_template(
        "admin_email_templates.html",
        templates=templates,
        template_keys=list(DEFAULT_EMAIL_TEMPLATES.keys()),
        active_page="templates",
    )


@admin_bp.route("/admin/calls/<int:log_id>", methods=["GET"])
@login_required
def call_detail(log_id: int):
    """Display full details for a specific call log."""

    log = CallLog.query.filter_by(id=log_id).first_or_404()
    _annotate_call_log(log)
    return render_template(
        "admin_call_detail.html",
        log=log,
        active_page=None,
    )


@admin_bp.route("/admin", methods=["GET"])
@login_required
def dashboard():
    """Admin landing page with quick links and stats."""

    total_calls = CallLog.query.count()
    latest_call = CallLog.query.order_by(CallLog.created_at.desc()).first()
    total_emails = EmailEvent.query.count()
    total_transfers = TransferEvent.query.count()
    recent_calls = CallLog.query.order_by(CallLog.created_at.desc()).limit(5).all()
    for call in recent_calls:
        _annotate_call_log(call)

    return render_template(
        "admin_home.html",
        stats={
            "total_calls": total_calls,
            "total_emails": total_emails,
            "total_transfers": total_transfers,
            "last_call_time": _format_eastern(latest_call.created_at) if latest_call else "—",
        },
        recent_calls=recent_calls,
        active_page="home",
    )

