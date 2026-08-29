from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("babybuddy", "0036_settings_dashboard_hidden_cards"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="dashboard_card_order",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Order in which cards are shown on child dashboards. Cards "
                    "not listed here are appended in their default order."
                ),
                verbose_name="Dashboard card order",
            ),
        ),
    ]
