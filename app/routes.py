"""Primary application routes for braselton_ai_agent."""

from __future__ import annotations

import base64
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request

from .ai_logic import handle_intent, process_audio_to_response
from .email_utils import send_billing_email
from .models import CallLog, db


main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def index() -> Any:
    """Basic service banner."""

    return jsonify(
        {
            "service": "braselton_ai_agent",
            "status": "online",
            "message": "Welcome to the Town of Braselton AI Phone Agent backend.",
        }
    )


@main_bp.route("/ws", methods=["GET", "POST"])
def livekit_websocket_placeholder() -> Any:
    """Placeholder endpoint for LiveKit WebSocket signaling.

    Flask's default WSGI server cannot terminate WebSocket upgrades. In production,
    use an ASGI-compatible server (e.g., Uvicorn) or LiveKit's serverless hooks.
    This route documents the expected request/response cycle for future work.
    """

    current_app.logger.info("LiveKit WebSocket endpoint invoked - implementation pending")
    return (
        jsonify(
            {
                "detail": (
                    "The LiveKit WebSocket bridge is not yet implemented. "
                    "Integrate the LiveKit Python SDK here to proxy media streams to OpenAI Realtime."
                )
            }
        ),
        501,
    )


@main_bp.route("/v1/process-audio", methods=["POST"])
def process_audio() -> Any:
    """Process audio payloads into AI-generated speech responses.

    Expected JSON payload:
    {
        "call_id": "string",
        "audio_b64": "base64-encoded audio chunk",
        "metadata": {...}
    }
    """

    payload: Dict[str, Any] = request.get_json(force=True, silent=False)
    audio_b64 = payload.get("audio_b64")
    call_id = payload.get("call_id", "unknown")

    if not audio_b64:
        return jsonify({"error": "audio_b64 field is required"}), 400

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except (ValueError, TypeError) as exc:
        current_app.logger.exception("Invalid base64 audio payload")
        return jsonify({"error": "invalid audio payload", "detail": str(exc)}), 400

    response_packet = process_audio_to_response(audio_bytes, call_id=call_id)
    return jsonify(response_packet)


@main_bp.route("/v1/intents", methods=["POST"])
def intents() -> Any:
    """Handle detected user intents from the AI pipeline."""

    payload: Dict[str, Any] = request.get_json(force=True, silent=False)
    user_text = payload.get("user_text", "")
    call_id = payload.get("call_id")
    caller_number = payload.get("caller_number")

    if not user_text:
        return jsonify({"error": "user_text is required"}), 400

    intent_result = handle_intent(user_text)

    if intent_result.email_template:
        send_billing_email(
            to_address=intent_result.email_template.recipient,
            subject=intent_result.email_template.subject,
            body=intent_result.email_template.body,
        )

    if call_id:
        log_call(
            call_id=call_id,
            caller_number=caller_number,
            transcript=user_text,
            sentiment_score=intent_result.sentiment_score,
            email_sent=bool(intent_result.email_template),
        )

    return jsonify(intent_result.to_dict())


def log_call(
    *,
    call_id: str | None,
    caller_number: str | None,
    transcript: str,
    sentiment_score: float | None,
    email_sent: bool,
) -> None:
    """Persist call interactions to the database."""

    if not call_id:
        current_app.logger.warning("Missing call_id for transcript logging; skipping persistence")
        return

    log_entry = CallLog(
        call_id=call_id,
        caller_number=caller_number,
        transcript=transcript,
        sentiment_score=sentiment_score,
        email_sent=email_sent,
    )
    db.session.add(log_entry)
    db.session.commit()

    if sentiment_score is not None and sentiment_score < -0.5:
        current_app.logger.warning("Negative sentiment detected for call %s: %s", call_id, sentiment_score)


