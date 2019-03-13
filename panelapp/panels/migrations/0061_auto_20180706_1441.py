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
# Generated by Django 2.0.6 on 2018-07-06 13:41

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("panels", "0060_auto_20180704_1647")]

    operations = [
        migrations.AddField(
            model_name="region",
            name="required_overlap_percentage",
            field=models.IntegerField(
                default=0,
                help_text="Required percent of overlap",
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="region",
            name="chromosome",
            field=models.CharField(
                choices=[
                    ("1", "1"),
                    ("2", "2"),
                    ("3", "3"),
                    ("4", "4"),
                    ("5", "5"),
                    ("6", "6"),
                    ("7", "7"),
                    ("8", "8"),
                    ("9", "9"),
                    ("10", "10"),
                    ("11", "11"),
                    ("12", "12"),
                    ("13", "13"),
                    ("14", "14"),
                    ("15", "15"),
                    ("16", "16"),
                    ("17", "17"),
                    ("18", "18"),
                    ("19", "19"),
                    ("20", "20"),
                    ("21", "21"),
                    ("22", "22"),
                    ("X", "X"),
                    ("Y", "Y"),
                ],
                max_length=8,
            ),
        ),
        migrations.AlterField(
            model_name="str",
            name="chromosome",
            field=models.CharField(
                choices=[
                    ("1", "1"),
                    ("2", "2"),
                    ("3", "3"),
                    ("4", "4"),
                    ("5", "5"),
                    ("6", "6"),
                    ("7", "7"),
                    ("8", "8"),
                    ("9", "9"),
                    ("10", "10"),
                    ("11", "11"),
                    ("12", "12"),
                    ("13", "13"),
                    ("14", "14"),
                    ("15", "15"),
                    ("16", "16"),
                    ("17", "17"),
                    ("18", "18"),
                    ("19", "19"),
                    ("20", "20"),
                    ("21", "21"),
                    ("22", "22"),
                    ("X", "X"),
                    ("Y", "Y"),
                ],
                max_length=8,
            ),
        ),
    ]
