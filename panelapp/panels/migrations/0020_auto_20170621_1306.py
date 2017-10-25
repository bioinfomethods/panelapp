# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-21 12:06
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0019_auto_20170621_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evaluation',
            name='phenotypes',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=512, null=True), blank=True, null=True, size=None),
        ),
        migrations.AlterField(
            model_name='evaluation',
            name='publications',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=512, null=True), blank=True, null=True, size=None),
        ),
    ]
