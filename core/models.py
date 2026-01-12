"""Database models for the Braselton AI Phone Agent (Django)."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class CallLog(models.Model):
    """Stores caller transcripts, metadata, and sentiment."""

    call_id = models.CharField(max_length=128, unique=True, db_index=True)
    caller_number = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    transcript = models.TextField()
    duration_seconds = models.IntegerField(null=True, blank=True)
    sentiment = models.CharField(max_length=20, blank=True)
    transferred = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "call_logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - convenience
        return f"CallLog({self.call_id})"


class EmailEvent(models.Model):
    """Represents an outbound email triggered during a call."""

    call = models.ForeignKey(
        CallLog,
        to_field="call_id",
        db_column="call_id",
        related_name="email_events",
        on_delete=models.CASCADE,
    )
    template_type = models.CharField(max_length=64)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "email_events"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"EmailEvent({self.template_type} -> {self.recipient})"


class TransferEvent(models.Model):
    """Represents a transfer attempt for a call."""

    call = models.ForeignKey(
        CallLog,
        to_field="call_id",
        db_column="call_id",
        related_name="transfer_events",
        on_delete=models.CASCADE,
    )
    target_number = models.CharField(max_length=64, blank=True, null=True)
    reason = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "transfer_events"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"TransferEvent({self.target_number})"


class EmailTemplateConfig(models.Model):
    """Stores editable email templates for admin customization."""

    template_type = models.CharField(max_length=64, unique=True, db_index=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "email_templates"
        ordering = ["template_type"]

    def __str__(self) -> str:  # pragma: no cover
        return f"EmailTemplateConfig({self.template_type})"


class PhoneConfiguration(models.Model):
    """Stores phone numbers used by the AI and transfer flows."""

    retell_ai_phone_number = models.CharField(max_length=32, blank=True, null=True)
    retell_ai_phone_label = models.CharField(max_length=128, blank=True, null=True)
    transfer_phone_numbers = models.JSONField(default=list, blank=True)
    transfer_phone_book = models.JSONField(default=list, blank=True)  # list of {"label": str, "number": str}
    transfer_request_email = models.EmailField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "phone_configuration"
        verbose_name = "Phone Configuration"
        verbose_name_plural = "Phone Configuration"

    def __str__(self) -> str:  # pragma: no cover
        return "PhoneConfiguration"


class InviteToken(models.Model):
    """One-time token for inviting a new user."""

    email = models.EmailField(db_index=True)
    token = models.CharField(max_length=128, unique=True, db_index=True)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    used = models.BooleanField(default=False)

    class Meta:
        db_table = "invite_tokens"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"InviteToken({self.email})"


class PasswordResetToken(models.Model):
    """One-time token for password reset."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    used = models.BooleanField(default=False)

    class Meta:
        db_table = "password_reset_tokens"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"PasswordResetToken({self.user_id})"


# We rely on Django's built-in User model for admin accounts.
User = settings.AUTH_USER_MODEL

