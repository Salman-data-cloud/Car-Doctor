# Generated by Django 5.2 on 2025-05-01 19:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("appointments", "0002_client_integrity_check_client_user_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="client", old_name="integrity_check", new_name="integrity_mac",
        ),
    ]
