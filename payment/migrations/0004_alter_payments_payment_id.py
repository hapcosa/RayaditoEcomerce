# Generated by Django 5.0.6 on 2024-11-25 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payment", "0003_alter_payments_order"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payments",
            name="payment_id",
            field=models.BigIntegerField(unique=True),
        ),
    ]