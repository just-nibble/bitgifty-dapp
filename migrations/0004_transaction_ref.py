# Generated by Django 3.2 on 2024-01-04 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dapp', '0003_transaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='ref',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
