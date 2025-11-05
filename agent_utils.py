"""Utilities for the LiveKit agent to interact with the Flask backend."""

import os
from typing import Optional

import requests


def log_conversation(
    call_id: str,
    caller_number: Optional[str],
    user_text: str,
    agent_response: str,
) -> None:
    """Send conversation transcript to Flask backend for storage."""
    
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    try:
        response = requests.post(
            f"{backend_url}/v1/intents",
            json={
                "call_id": call_id,
                "caller_number": caller_number,
                "user_text": user_text,
            },
            timeout=5,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to log conversation: {e}")
        return None


def detect_intent(user_text: str) -> dict:
    """Detect user intent using the Flask backend."""
    
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    try:
        response = requests.post(
            f"{backend_url}/v1/intents",
            json={"user_text": user_text},
            timeout=5,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to detect intent: {e}")
        return {"intent": "unknown"}


def should_transfer_to_human(intent_data: dict) -> bool:
    """Check if the call should be transferred to a human agent."""
    
    return intent_data.get("intent") == "transfer"


def should_send_email(intent_data: dict) -> bool:
    """Check if an email should be sent based on intent."""
    
    return "email" in intent_data

