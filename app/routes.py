"""Retell AI webhook handlers for Braselton AI Phone Agent.

This integration layer receives webhooks from Retell AI and:
1. Sends emails via SMTP2Go when agent needs to email caller
2. Stores call transcripts for 5-year retention (GA state law LG 20-022)
"""

from __future__ import annotations

from typing import Any

from flask import Blueprint, current_app, jsonify, request

from .email_utils import send_billing_email
from .models import CallLog, db

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def index() -> Any:
    """Basic service banner."""
    
    return jsonify(
        {
            "service": "braselton_retell_integration",
            "status": "online",
            "message": "Town of Braselton AI Phone Agent - Retell AI Integration Layer",
        }
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
        if call_log:
            call_log.email_sent = True
            db.session.commit()
        
        current_app.logger.info("Email sent for call %s to %s", call_id, user_email)
        
        return jsonify({"status": "sent", "email_type": email_type})
        
    except Exception as e:
        current_app.logger.exception("Failed to send email")
        return jsonify({"error": str(e)}), 500


@main_bp.route("/webhook/transcript", methods=["POST"])
def store_transcript() -> Any:
    """Store call transcript for 5-year retention.
    
    Expected payload from Retell AI on call end:
    {
        "call_id": "string",
        "caller_phone": "string",
        "duration_seconds": number,
        "transcript": "full conversation text",
        "timestamp": "ISO datetime",
        "transferred": boolean,
        "sentiment": "positive" | "neutral" | "negative"
    }
    """
    
    try:
        data = request.get_json(force=True, silent=False)
        
        call_id = data.get("call_id")
        if not call_id:
            return jsonify({"error": "call_id is required"}), 400
        
        transcript = data.get("transcript", "")
        if not transcript:
            return jsonify({"error": "transcript is required"}), 400
        
        # Check if already exists (idempotency)
        existing = CallLog.query.filter_by(call_id=call_id).first()
        if existing:
            current_app.logger.info("Call %s already logged, skipping", call_id)
            return jsonify({"status": "already_exists"})
        
        # Create call log entry
        call_log = CallLog(
            call_id=call_id,
            caller_number=data.get("caller_phone"),
            transcript=transcript,
            duration_seconds=data.get("duration_seconds"),
            sentiment=data.get("sentiment", "neutral"),
            transferred=data.get("transferred", False),
            email_sent=False,  # Will be updated by email webhook
        )
        
        db.session.add(call_log)
        db.session.commit()
        
        current_app.logger.info(
            "Stored transcript for call %s (duration: %ds, sentiment: %s)",
            call_id,
            call_log.duration_seconds,
            call_log.sentiment,
        )
        
        return jsonify({"status": "stored", "id": call_log.id})
        
    except Exception as e:
        current_app.logger.exception("Failed to store transcript")
        return jsonify({"error": str(e)}), 500


def get_email_template(email_type: str) -> tuple[str, str]:
    """Get email subject and body based on type.
    
    Returns:
        Tuple of (subject, body)
    """
    
    website_url = current_app.config.get("TOWN_WEBSITE_URL", "https://braselton.net")
    
    templates = {
        "payment_link": (
            "Braselton Utilities - Online Payment Link",
            f"""Hello,

Thank you for contacting the Town of Braselton Utilities Department.

To pay your utility bill online, please visit:
{website_url}/pay

Payment options:
- Credit/debit card
- E-check

You can also pay in person at Town Hall (cash, check, or money order).

Hours: Monday-Friday, 8:00 AM - 5:00 PM
Address: 6111 Winder Highway, Braselton, GA 30517

Questions? Call (770) 867-4488

Town of Braselton Utilities
""",
        ),
        "adjustment_form": (
            "Braselton Utilities - Request for Adjustment Form",
            f"""Hello,

Please find the Request for Adjustment form here:
{website_url}/utilities/adjustment-form

Complete and return to:
- Email: utilitybilling@braselton.net
- In person: Braselton Town Hall

We'll review your request within 3-5 business days.

Questions? Call (770) 867-4488

Town of Braselton Utilities
""",
        ),
        "general_info": (
            "Braselton Utilities - Contact Information",
            f"""Hello,

Thank you for contacting the Town of Braselton Utilities Department.

For more information, please visit our website:
{website_url}

Contact Us:
Phone: (770) 867-4488
Email: utilitybilling@braselton.net
Address: 6111 Winder Highway, Braselton, GA 30517

Hours: Monday-Friday, 8:00 AM - 5:00 PM

Town of Braselton Utilities
""",
        ),
    }
    
    return templates.get(email_type, templates["general_info"])
