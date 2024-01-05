# Generated by Django 3.2 on 2024-01-04 21:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dapp', '0002_giftcard_sender_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.FloatField(default=0.0)),
                ('currency', models.CharField(default='naira', max_length=255)),
                ('currency_type', models.CharField(default='fiat', max_length=255)),
                ('crypto_amount', models.FloatField(default=0.0)),
                ('bank_name', models.CharField(blank=True, max_length=255, null=True)),
                ('account_name', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(default='pending', max_length=255)),
                ('time', models.DateTimeField(auto_now_add=True, null=True)),
                ('transaction_type', models.CharField(max_length=255, null=True)),
                ('transaction_hash', models.CharField(max_length=255, null=True)),
                ('wallet_address', models.CharField(max_length=255, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
            ],
        ),
    ]
