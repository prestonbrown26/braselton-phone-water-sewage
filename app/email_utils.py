"""Email helper utilities for SMTP2Go integration."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from flask import current_app


def send_billing_email(*, to_address: str, subject: str, body: str) -> None:
    """Send outbound emails via SMTP2Go."""

    smtp_host = current_app.config["SMTP2GO_SMTP_HOST"]
    smtp_port = current_app.config["SMTP2GO_SMTP_PORT"]
    username = current_app.config["SMTP2GO_USERNAME"]
    password = current_app.config["SMTP2GO_PASSWORD"]
    stub_mode = current_app.config.get("EMAIL_STUB_MODE", False)

    if stub_mode:
        current_app.logger.info(
            "EMAIL_STUB_MODE enabled - would send email to %s with subject '%s'. Body:\n%s",
            to_address,
            subject,
            body,
        )
        return

    if not all([smtp_host, smtp_port, username, password]):
        current_app.logger.warning(
            "SMTP2Go credentials are not fully configured; skipping email send"
        )
        return

    from_address = current_app.config.get("EMAIL_FROM_ADDRESS", "utilitybilling@braselton.net")
    
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address
    msg.set_content(body)

    current_app.logger.info("Sending SMTP2Go email to %s", to_address)
    with smtplib.SMTP(smtp_host, smtp_port) as client:
        client.starttls()
        client.login(username, password)
        client.send_message(msg)


