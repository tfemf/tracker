# Generated by Django 5.0.1 on 2024-01-25 14:15

import colorfield.fields
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tracking", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Route",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "type",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "Tram, Streetcar, Light rail"),
                            (1, "Subway, Metro"),
                            (2, "Rail"),
                            (3, "Bus"),
                            (4, "Ferry"),
                            (5, "Cable tram"),
                            (6, "Aerial lift"),
                            (7, "Funicular"),
                            (11, "Trolleybus"),
                            (12, "Monorail"),
                        ]
                    ),
                ),
                ("url", models.URLField(blank=True, null=True)),
                (
                    "color",
                    colorfield.fields.ColorField(
                        blank=True,
                        default=None,
                        image_field=None,
                        max_length=25,
                        null=True,
                        samples=None,
                    ),
                ),
                (
                    "text_color",
                    colorfield.fields.ColorField(
                        blank=True,
                        default=None,
                        image_field=None,
                        max_length=25,
                        null=True,
                        samples=None,
                    ),
                ),
                ("order", models.PositiveIntegerField(blank=True, default=0)),
            ],
            options={
                "ordering": ["order"],
            },
        ),
        migrations.AddField(
            model_name="stop",
            name="internal",
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AddField(
            model_name="stop",
            name="url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="stop",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
    ]
