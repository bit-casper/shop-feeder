# Generated by Django 5.1.6 on 2025-03-06 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feed',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
