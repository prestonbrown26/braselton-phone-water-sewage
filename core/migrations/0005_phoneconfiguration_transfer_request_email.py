from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_invite_and_reset_tokens"),
    ]

    operations = [
        migrations.AddField(
            model_name="phoneconfiguration",
            name="transfer_request_email",
            field=models.EmailField(blank=True, null=True, max_length=254),
        ),
    ]

