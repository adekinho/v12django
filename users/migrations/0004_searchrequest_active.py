# Generated by Django 5.2 on 2025-05-02 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_requestresponse"),
    ]

    operations = [
        migrations.AddField(
            model_name="searchrequest",
            name="active",
            field=models.BooleanField(default=True),
        ),
    ]
