"""Retell AI webhook handlers for Braselton AI Phone Agent.

This integration layer receives webhooks from Retell AI and:
1. Sends emails via SMTP2Go when agent needs to email caller
2. Stores call transcripts for 5-year retention (GA state law LG 20-022)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, current_app, jsonify, render_template, request

from .email_templates import ensure_email_template
from .email_utils import send_billing_email
from .models import CallLog, EmailEvent, EmailTemplateConfig, TransferEvent, db

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def index() -> Any:
    """Public landing page with key contact info."""

    agent_number = current_app.config.get("AGENT_PHONE_NUMBER", "Not configured")
    transfer_numbers = current_app.config.get("TRANSFER_NUMBERS", [])
    return render_template(
        "home.html",
        agent_number=agent_number,
        transfer_numbers=transfer_numbers,
    )


@main_bp.route("/webhook/email", methods=["POST"])
def handle_email_request() -> Any:
    """Handle email sending requests from Retell AI agent.
    
    Expected payload from Retell AI custom action:
    {
        "call_id": "string",
        "caller_phone": "string",
        "email_type": "payment_link" | "adjustment_form" | "general_info",
        "user_email": "user@example.com"
    }
    """
    
    try:
        data = request.get_json(force=True, silent=False)
        
        # Log the incoming data for debugging
        current_app.logger.info("Received email webhook data: %s", data)
        
        # Retell sends data nested under 'args'
        args = data.get("args", data)
        
        email_type = args.get("email_type", "payment_link")
        user_email = args.get("user_email")
        call_id = args.get("call_id", data.get("call", {}).get("call_id", "unknown"))
        
        if not user_email:
            current_app.logger.error("Missing user_email in webhook data: %s", data)
            return jsonify({"error": "user_email is required"}), 400
        
        # Get email template based on type
        subject, body = get_email_template(email_type)
        
        # Send via SMTP2Go
        send_billing_email(
            to_address=user_email,
            subject=subject,
            body=body,
        )
        
        # Mark email sent in call log if it exists
        call_log = CallLog.query.filter_by(call_id=call_id).first()
        if not call_log:
            placeholder_text = (
                "Call log placeholder created automatically because the email webhook "
                "arrived before the transcript webhook."
            )
            call_log = CallLog(
                call_id=call_id,
                caller_number=args.get("caller_phone"),
                transcript=placeholder_text,
                sentiment="neutral",
                transferred=False,
                email_sent=False,
                created_at=datetime.utcnow(),
            )
            db.session.add(call_log)
            current_app.logger.warning(
                "Created placeholder call log for %s because email arrived before transcript.",
                call_id,
            )
        call_log.email_sent = True
        email_event = EmailEvent(
            call_id=call_id,
            template_type=email_type,
            recipient=user_email,
            subject=subject,
            body=body,
        )
        db.session.add(email_event)
        db.session.commit()
        
        current_app.logger.info("Email sent for call %s to %s", call_id, user_email)
        
        return jsonify({"status": "sent", "email_type": email_type})
        
    except Exception as e:
        current_app.logger.exception("Failed to send email")
        return jsonify({"error": str(e)}), 500


@main_bp.route("/webhook/transcript", methods=["POST"])
def retell_transcript_webhook() -> Any:
    """Handle Retell AI agent-level webhook events."""

    try:
        payload = request.get_json(force=True, silent=False)
        current_app.logger.info("Received transcript webhook payload: %s", payload)

        event_type = payload.get("event")
        if event_type != "call_ended":
            current_app.logger.info("Ignoring unsupported event '%s'", event_type)
            return jsonify({"status": "ignored", "event": event_type}), 200

        call_data = payload.get("call", {})
        call_id = call_data.get("call_id")
        if not call_id:
            return jsonify({"error": "call.call_id is required"}), 400

        transcript = (call_data.get("transcript") or "").strip()

        # Retell may deliver an empty transcript if conversation summary
        # is still being generated. Fall back to transcript_with_tool_calls
        # so we can still archive the call for compliance.
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
            transcript = (
                "Transcript not provided by Retell. "
                + (f"Reference recording: {recording_url}" if recording_url else "No recording URL supplied.")
            )

        # Prevent duplicate inserts if Retell retries
        existing = CallLog.query.filter_by(call_id=call_id).first()
        if existing:
            current_app.logger.info("Call %s already logged; acking webhook", call_id)
            return jsonify({"status": "already_exists"}), 200

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

        call_log = CallLog(
            call_id=call_id,
            caller_number=caller_number,
            transcript=transcript,
            duration_seconds=duration_seconds,
            sentiment="neutral",
            transferred=False,
            email_sent=False,
            created_at=call_end_dt,
        )

        db.session.add(call_log)
        db.session.commit()

        current_app.logger.info(
            "Stored call %s (duration=%s sec, caller=%s)",
            call_id,
            duration_seconds,
            caller_number,
        )

        return jsonify({"status": "ok"}), 200

    except Exception as exc:
        current_app.logger.exception("Failed to handle transcript webhook")
        return jsonify({"error": str(exc)}), 500


@main_bp.route("/webhook/transfer", methods=["POST"])
def retell_transfer_webhook() -> Any:
    """Record transfer attempts initiated by the agent."""

    try:
        data = request.get_json(force=True, silent=False)
        current_app.logger.info("Received transfer webhook payload: %s", data)

        call_id = data.get("call_id")
        if not call_id:
            return jsonify({"error": "call_id is required"}), 400

        target_number = data.get("target_number")
        reason = data.get("reason")
        notes = data.get("notes") or data.get("details")

        event = TransferEvent(
            call_id=call_id,
            target_number=target_number,
            reason=reason,
            notes=notes,
        )
        db.session.add(event)

        call_log = CallLog.query.filter_by(call_id=call_id).first()
        if call_log:
            call_log.transferred = True

        db.session.commit()
        current_app.logger.info(
            "Logged transfer for call %s → %s", call_id, target_number or "unknown target"
        )
        return jsonify({"status": "ok"}), 200

    except Exception as exc:
        current_app.logger.exception("Failed to handle transfer webhook")
        return jsonify({"error": str(exc)}), 500


def get_email_template(email_type: str) -> tuple[str, str]:
    """Return the stored email template, creating defaults if needed."""

    template = EmailTemplateConfig.query.filter_by(template_type=email_type).first()
    if not template:
        template = ensure_email_template(email_type)
    return template.subject, template.body
