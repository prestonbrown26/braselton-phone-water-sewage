"""Shared helpers for formatting and webhook auth."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.http import HttpRequest


EASTERN_TZ = ZoneInfo("America/New_York")


def format_eastern(dt: datetime | None) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(EASTERN_TZ).strftime("%Y-%m-%d %I:%M %p ET")


def verify_webhook_secret(request: HttpRequest) -> bool:
    """Verify a shared secret for incoming webhooks (defense against spoofing)."""

    expected = (getattr(settings, "WEBHOOK_SHARED_SECRET", "") or "").strip()
    if not expected:
        logger.warning("WEBHOOK_SHARED_SECRET not configured; rejecting webhook.")
        return False

    provided = (
        request.headers.get("X-Webhook-Secret")
        or request.headers.get("X-Webhook-Token")
        or request.GET.get("token")
        or request.GET.get("secret")
        or request.GET.get("webhook_secret")
    )
    return provided == expected

