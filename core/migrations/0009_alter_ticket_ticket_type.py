from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_alter_ticket_ticket_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ticket",
            name="ticket_type",
            field=models.CharField(
                choices=[
                    ("feature", "Feature Request"),
                    ("bug", "Bug"),
                    ("kb_update", "Knowledge Base Update"),
                    ("transfer_change", "Transfer Number Change"),
                    ("other", "Other"),
                ],
                default="feature",
                max_length=20,
            ),
        ),
    ]

