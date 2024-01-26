# Generated by Django 5.0.1 on 2024-01-25 16:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tracking", "0003_vehicle_alter_route_url_alter_stop_url_journey_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journey",
            name="direction",
            field=models.PositiveSmallIntegerField(
                blank=True, choices=[(0, "Inbound"), (1, "Outbound")], null=True
            ),
        ),
    ]
