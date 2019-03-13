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
# Generated by Django 2.0.6 on 2018-06-19 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0052_auto_20180615_1147'),
    ]

    operations = [
        migrations.AddField(
            model_name='genepanelsnapshot',
            name='child_panels',
            field=models.ManyToManyField(to='panels.GenePanelSnapshot'),
        ),
    ]
