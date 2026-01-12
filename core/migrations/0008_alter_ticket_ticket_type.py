from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_ticket"),
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
                    ("other", "Other"),
                ],
                default="feature",
                max_length=20,
            ),
        ),
    ]

