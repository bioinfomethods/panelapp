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
# Generated by Django 2.0.6 on 2018-07-24 11:45

from django_extensions.db.fields import AutoSlugField
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("panels", "0062_auto_20180713_1155")]

    operations = [
        migrations.CreateModel(
            name="PanelType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=128)),
                (
                    "slug",
                    AutoSlugField(editable=False, populate_from="name", unique=True),
                ),
                ("description", models.TextField()),
            ],
        ),
        migrations.AlterField(
            model_name="region",
            name="name",
            field=models.CharField(help_text="Region ID", max_length=128),
        ),
        migrations.AlterField(
            model_name="region",
            name="verbose_name",
            field=models.CharField(
                blank=True, help_text="Region Name", max_length=256, null=True
            ),
        ),
        migrations.AddField(
            model_name="genepanel",
            name="types",
            field=models.ManyToManyField(to="panels.PanelType"),
        ),
    ]
