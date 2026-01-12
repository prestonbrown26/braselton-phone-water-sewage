from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("webhook/email", views.webhook_email, name="webhook-email"),
    path("webhook/transcript", views.webhook_transcript, name="webhook-transcript"),
    path("webhook/transfer", views.webhook_transfer, name="webhook-transfer"),
    # Admin
    path("admin/login/", views.admin_login, name="admin-login"),
    path("admin/logout/", views.admin_logout, name="admin-logout"),
    path("forgot-password/", views.forgot_password, name="forgot-password"),
    path("reset-password/", views.reset_password, name="reset-password"),
    path("accept-invite/", views.accept_invite, name="accept-invite"),
    path("admin/", views.admin_dashboard, name="admin-dashboard"),
    path("admin/calls/", views.admin_calls, name="admin-calls"),
    path("admin/transcripts/", views.admin_transcripts, name="admin-transcripts"),
    path("admin/export/", views.admin_export, name="admin-export-calls"),
    path("admin/email-templates/", views.manage_email_templates, name="admin-manage-email-templates"),
    path("admin/settings/", views.admin_settings, name="admin-settings"),
    path("admin/feedback/", views.admin_feedback, name="admin-feedback"),
    path("admin/feedback/<int:ticket_id>/", views.admin_ticket_detail, name="admin-ticket-detail"),
    path("admin/calls/<int:log_id>/", views.call_detail, name="admin-call-detail"),
]

