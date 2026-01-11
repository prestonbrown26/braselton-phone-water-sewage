from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PhoneConfiguration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("retell_ai_phone_number", models.CharField(blank=True, max_length=32, null=True)),
                ("transfer_phone_numbers", models.JSONField(blank=True, default=list)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Phone Configuration",
                "verbose_name_plural": "Phone Configuration",
                "db_table": "phone_configuration",
            },
        ),
    ]
