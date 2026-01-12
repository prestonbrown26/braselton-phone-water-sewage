from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_phoneconfiguration_labels"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="InviteToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, db_index=True)),
                ("token", models.CharField(max_length=128, unique=True, db_index=True)),
                ("is_staff", models.BooleanField(default=True)),
                ("is_superuser", models.BooleanField(default=False)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("used", models.BooleanField(default=False)),
                (
                    "invited_by",
                    models.ForeignKey(
                        null=True,
                        blank=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "invite_tokens",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PasswordResetToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.CharField(max_length=128, unique=True, db_index=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("used", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reset_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "password_reset_tokens",
                "ordering": ["-created_at"],
            },
        ),
    ]

