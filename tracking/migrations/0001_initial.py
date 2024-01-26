# Generated by Django 5.0.1 on 2024-01-25 13:51

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Stop",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        editable=False, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("code", models.CharField(blank=True, max_length=255, null=True)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, null=True)),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
            ],
        ),
    ]