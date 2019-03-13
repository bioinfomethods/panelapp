##
## Copyright (c) 2016-2019 Genomics England Ltd.
##
## This file is part of PanelApp
## (see https://panelapp.genomicsengland.co.uk).
##
## Licensed to the Apache Software Foundation (ASF) under one
## or more contributor license agreements.  See the NOTICE file
## distributed with this work for additional information
## regarding copyright ownership.  The ASF licenses this file
## to you under the Apache License, Version 2.0 (the
## "License"); you may not use this file except in compliance
## with the License.  You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing,
## software distributed under the License is distributed on an
## "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
## KIND, either express or implied.  See the License for the
## specific language governing permissions and limitations
## under the License.
##
# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-30 13:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_auto_20170530_1414'),
        ('panels', '0004_auto_20170526_1056'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='genepanelentrysnapshot',
            options={'get_latest_by': 'created', 'ordering': ['-created']},
        ),
        migrations.AlterModelOptions(
            name='genepanelsnapshot',
            options={'get_latest_by': 'created', 'ordering': ['-created', '-major_version', '-minor_version']},
        ),
        migrations.AlterModelOptions(
            name='trackrecord',
            options={'ordering': ('-created',)},
        ),
        migrations.RenameField(
            model_name='evidence',
            old_name='source_name',
            new_name='name',
        ),
        migrations.RemoveField(
            model_name='evidence',
            name='type',
        ),
        migrations.AddField(
            model_name='evidence',
            name='legacy_type',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='evidence',
            name='reviewer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.Reviewer'),
        ),
        migrations.AddField(
            model_name='genepanelentrysnapshot',
            name='created',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created'),
        ),
        migrations.AddField(
            model_name='genepanelentrysnapshot',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified'),
        ),
        migrations.AddField(
            model_name='genepanelentrysnapshot',
            name='saved_gel_status',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='trackrecord',
            name='curator_status',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='trackrecord',
            name='gel_status',
            field=models.IntegerField(default=0),
        ),
    ]
