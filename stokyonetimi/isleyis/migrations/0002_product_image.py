# Generated by Django 5.0.6 on 2024-12-21 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('isleyis', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='products/'),
        ),
    ]
