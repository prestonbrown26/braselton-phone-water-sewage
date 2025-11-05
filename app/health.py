"""Health check endpoint."""

from __future__ import annotations

from flask import Blueprint, jsonify


health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health() -> tuple[dict[str, str], int]:
    """Simple health probe for uptime monitoring."""

    return jsonify({"status": "ok"}), 200

