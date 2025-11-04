"""Service monitoring utilities and health endpoints."""

from __future__ import annotations

import requests
from flask import Blueprint, current_app, jsonify


monitor_bp = Blueprint("monitor", __name__)


@monitor_bp.route("/health", methods=["GET"])
def health() -> tuple[dict[str, str], int]:
    """Simple health probe for uptime monitoring."""

    return jsonify({"status": "ok"}), 200


def alert_teams(message: str) -> None:
    """Send an alert to the configured Microsoft Teams channel."""

    webhook_url = current_app.config.get("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        current_app.logger.debug("TEAMS_WEBHOOK_URL not configured; skipping Teams alert")
        return

    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status()
        current_app.logger.info("Sent Teams alert: %s", message)
    except requests.RequestException as exc:  # pragma: no cover - network dependent
        current_app.logger.exception("Failed to send Teams alert: %s", exc)


