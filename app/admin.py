"""Administrative routes for viewing call logs."""

from __future__ import annotations

import csv
import io

from flask import Blueprint, Response, current_app, redirect, render_template, request, session, url_for, flash
from flask_login import login_required, login_user, logout_user, UserMixin

from . import db, login_manager
from .models import CallLog


admin_bp = Blueprint("admin", __name__)


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
            return redirect(next_page or url_for("admin.search_transcripts"))
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
    return render_template("admin_calls.html", logs=logs)


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
        from datetime import datetime
        try:
            search_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(db.func.date(CallLog.created_at) == search_date)
        except ValueError:
            pass  # Invalid date format, ignore
    
    results = query.order_by(CallLog.created_at.desc()).limit(100).all()
    
    return render_template("admin_transcripts.html", results=results, search_params={
        "call_id": call_id or "",
        "phone": phone or "",
        "date": date or "",
    })


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


