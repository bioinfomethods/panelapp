# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-16 10:09
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0014_auto_20170615_0953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='genepanelsnapshot',
            name='old_panels',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), blank=True, null=True, size=None),
        ),
    ]
