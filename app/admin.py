"""Administrative routes for viewing call logs."""

from __future__ import annotations

import csv
import io
from functools import wraps

from flask import Blueprint, Response, current_app, render_template, request

from .models import CallLog


admin_bp = Blueprint("admin", __name__)


def requires_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        expected_user = current_app.config.get("ADMIN_USERNAME")
        expected_pass = current_app.config.get("ADMIN_PASSWORD")

        if not auth or auth.username != expected_user or auth.password != expected_pass:
            return Response(
                "Authentication required",
                401,
                {"WWW-Authenticate": 'Basic realm="Braselton Admin"'},
            )

        return func(*args, **kwargs)

    return wrapper


@admin_bp.route("/admin/calls", methods=["GET"])
@requires_auth
def admin_calls():
    """Render recent call logs for the admin portal."""

    logs = CallLog.query.order_by(CallLog.created_at.desc()).limit(200).all()
    return render_template("admin_calls.html", logs=logs)


@admin_bp.route("/admin/export", methods=["GET"])
@requires_auth
def export_calls():
    """Stream call logs as CSV for archival or compliance."""

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "call_id", "caller_number", "transcript", "sentiment_score", "email_sent", "created_at"])

    for log in CallLog.query.order_by(CallLog.created_at.desc()).all():
        writer.writerow(
            [
                log.id,
                log.call_id,
                log.caller_number,
                log.transcript,
                log.sentiment_score,
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


