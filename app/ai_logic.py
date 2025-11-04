"""AI dialogue pipeline for the Braselton AI Phone Agent."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Dict, Optional

from flask import current_app


@dataclass
class EmailTemplate:
    """Represents an outbound email request."""

    recipient: str
    subject: str
    body: str


@dataclass
class IntentResult:
    """Structured response from intent handling."""

    intent: str
    response_text: str
    sentiment_score: float
    email_template: Optional[EmailTemplate] = None
    alert_message: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        data = {
            "intent": self.intent,
            "response_text": self.response_text,
            "sentiment_score": self.sentiment_score,
            "metadata": self.metadata,
        }

        if self.email_template:
            data["email"] = {
                "recipient": self.email_template.recipient,
                "subject": self.email_template.subject,
            }

        if self.alert_message:
            data["alert"] = self.alert_message

        return data


def process_audio_to_response(audio_bytes: bytes, *, call_id: str) -> Dict[str, object]:
    """Convert caller audio into an AI-generated spoken response."""

    transcript_text = transcribe_audio(audio_bytes, call_id=call_id)
    ai_response_text = generate_response(transcript_text, call_id=call_id)
    audio_output = synthesize_speech(ai_response_text, call_id=call_id)

    encoded_audio = base64.b64encode(audio_output).decode("utf-8")
    return {
        "transcript": transcript_text,
        "response_text": ai_response_text,
        "response_audio_b64": encoded_audio,
    }


def transcribe_audio(audio_bytes: bytes, *, call_id: str) -> str:
    """Send audio to OpenAI Realtime STT and return the transcription."""

    current_app.logger.debug("Transcribing audio for call %s (%s bytes)", call_id, len(audio_bytes))

    # TODO: Integrate with OpenAI's Realtime API for streaming transcription.
    return "This is a placeholder transcription while STT is implemented."


def generate_response(user_text: str, *, call_id: str) -> str:
    """Generate an AI response using GPT-4o Realtime."""

    current_app.logger.debug("Generating response for call %s with text '%s'", call_id, user_text)

    # TODO: Replace with OpenAI GPT-4o Realtime completion logic.
    return "Thanks for calling Braselton Utilities. How can I assist you further?"


def synthesize_speech(response_text: str, *, call_id: str) -> bytes:
    """Convert response text into speech using OpenAI TTS."""

    current_app.logger.debug("Synthesizing speech for call %s", call_id)

    # TODO: Replace with OpenAI TTS audio generation.
    return b""  # Placeholder: return raw audio bytes when integrated.


def handle_intent(user_text: str) -> IntentResult:
    """Lightweight intent routing for billing, escalation, and FAQs."""

    normalized = user_text.lower()
    sentiment = estimate_sentiment(normalized)

    if "pay" in normalized and "bill" in normalized:
        email_template = EmailTemplate(
            recipient="utilitybilling@braselton.net",
            subject="Utility Billing Payment Link",
            body=(
                "Hello,\n\nThank you for contacting the Town of Braselton Utilities. "
                "To pay your bill online, please visit https://braselton.net/pay.\n\n"
                "If you have questions, reply to this email or call 706-555-0100.\n"
            ),
        )
        return IntentResult(
            intent="pay_bill",
            response_text="I've emailed you a secure link to pay your utility bill.",
            sentiment_score=sentiment,
            email_template=email_template,
            metadata={"action": "send_email"},
        )

    if "talk" in normalized and ("person" in normalized or "representative" in normalized):
        return IntentResult(
            intent="transfer",
            response_text="Let me connect you with a member of our utilities team.",
            sentiment_score=sentiment,
            metadata={"action": "transfer_human"},
        )

    return IntentResult(
        intent="general_question",
        response_text=(
            "I'm here to help with Braselton utilities. You can ask about billing, "
            "outages, or service updates."
        ),
        sentiment_score=sentiment,
    )


def estimate_sentiment(user_text: str) -> float:
    """Naive sentiment heuristic; replace with ML/NLP integration later."""

    # TODO: Replace with OpenAI sentiment classification or Azure ML as needed.
    negative_tokens = {"angry", "upset", "frustrated", "mad", "bad"}
    positive_tokens = {"great", "thanks", "appreciate", "good", "happy"}

    score = 0.0
    for token in negative_tokens:
        if token in user_text:
            score -= 0.2
    for token in positive_tokens:
        if token in user_text:
            score += 0.2
    return max(min(score, 1.0), -1.0)


