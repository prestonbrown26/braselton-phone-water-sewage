"""Email helper utilities for SMTP2Go integration via Django."""

from __future__ import annotations

from typing import Sequence

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.module_loading import import_string

import logging

logger = logging.getLogger(__name__)


def _get_backend_class():
    """Resolve the configured email backend class."""

    backend_path = settings.EMAIL_BACKEND
    backend_cls = import_string(backend_path)
    return backend_cls


def send_billing_email(*, to_address: str, subject: str, body: str) -> None:
    """Send outbound emails via SMTP2Go (or stub)."""

    stub_mode = getattr(settings, "EMAIL_STUB_MODE", False)
    if stub_mode:
        logger.info("EMAIL_STUB_MODE enabled - would send email to %s with subject '%s'. Body:\n%s", to_address, subject, body)
        return

    if not all([settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD]):
        logger.warning("SMTP2Go credentials are not fully configured; skipping email send")
        return

    from_address = getattr(settings, "EMAIL_FROM_ADDRESS", "utilitybilling@braselton.net")
    email = EmailMessage(subject=subject, body=body, from_email=from_address, to=[to_address])

    backend_cls = _get_backend_class()
    backend = backend_cls(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        use_ssl=False,
    )

    logger.info("Sending SMTP2Go email to %s", to_address)
    try:
        backend.send_messages([email])
    except Exception as exc:  # pragma: no cover - network dependent
        logger.error("Failed to send email to %s: %s", to_address, exc)
        raise

