from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_phoneconfiguration"),
    ]

    operations = [
        migrations.AddField(
            model_name="phoneconfiguration",
            name="retell_ai_phone_label",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="phoneconfiguration",
            name="transfer_phone_book",
            field=models.JSONField(blank=True, default=list),
        ),
    ]

