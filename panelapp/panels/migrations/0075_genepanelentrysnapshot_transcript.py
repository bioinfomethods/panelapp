# Generated by Django 2.1.10 on 2019-10-25 16:10

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0074_historicalsnapshot_signed_off_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='genepanelentrysnapshot',
            name='transcript',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=255, null=True), blank=True, null=True, size=None),
        ),
    ]
