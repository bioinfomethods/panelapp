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
# Generated by Django 1.11.1 on 2017-05-26 09:41
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("panels", "0002_gene"),
    ]

    operations = [
        migrations.CreateModel(
            name="Activity",
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
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("gene_symbol", models.CharField(max_length=255)),
                ("text", models.CharField(max_length=255)),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Comment",
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
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("comment", models.TextField()),
                ("flagged", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Evaluation",
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
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("rating", models.CharField(max_length=255)),
                ("transcript", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "mode_of_pathogenicity",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "publications",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            blank=True, max_length=255, null=True
                        ),
                        size=None,
                    ),
                ),
                (
                    "phenotypes",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            blank=True, max_length=255, null=True
                        ),
                        size=None,
                    ),
                ),
                ("moi", models.CharField(blank=True, max_length=255, null=True)),
                ("current_diagnostic", models.BooleanField(default=False)),
                ("version", models.CharField(blank=True, max_length=255, null=True)),
                ("comments", models.ManyToManyField(to="panels.Comment")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Evidence",
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
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("source_name", models.CharField(max_length=255)),
                ("rating", models.IntegerField()),
                ("comment", models.CharField(max_length=255)),
                ("type", models.CharField(max_length=255)),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="GenePanel",
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
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("approved", models.BooleanField(default=False)),
                ("promoted", models.BooleanField(default=False)),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="GenePanelEntrySnapshot",
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
                ("gene", django.contrib.postgres.fields.jsonb.JSONField()),
                ("moi", models.CharField(max_length=255)),
                ("penetrance", models.CharField(max_length=255)),
                (
                    "publications",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=255), size=None
                    ),
                ),
                (
                    "phenotypes",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=255), size=None
                    ),
                ),
                (
                    "tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=30), size=None
                    ),
                ),
                ("flagged", models.BooleanField(default=False)),
                ("ready", models.BooleanField(default=False)),
                ("mode_of_pathogenicity", models.CharField(max_length=255)),
                ("comments", models.ManyToManyField(to="panels.Comment")),
                ("contributors", models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ("evaluation", models.ManyToManyField(to="panels.Evaluation")),
                ("evidence", models.ManyToManyField(to="panels.Evidence")),
                (
                    "gene_core",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="panels.Gene"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GenePanelSnapshot",
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
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("major_version", models.IntegerField(default=0)),
                ("minor_version", models.IntegerField(default=0)),
                ("version_comment", models.TextField(null=True)),
                (
                    "old_panels",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=255), size=None
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Level4Title",
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
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("level3title", models.CharField(max_length=255)),
                ("level2title", models.CharField(max_length=255)),
                (
                    "omim",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=255), size=None
                    ),
                ),
                (
                    "orphanet",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=255), size=None
                    ),
                ),
                (
                    "hpo",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=255), size=None
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TrackRecord",
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
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("issue_type", models.CharField(max_length=255)),
                ("issue_description", models.CharField(max_length=255)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.AddField(
            model_name="genepanelsnapshot",
            name="level4title",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="panels.Level4Title"
            ),
        ),
        migrations.AddField(
            model_name="genepanelsnapshot",
            name="panel",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="panels.GenePanel"
            ),
        ),
        migrations.AddField(
            model_name="genepanelentrysnapshot",
            name="panel",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="panels.GenePanelSnapshot",
            ),
        ),
        migrations.AddField(
            model_name="genepanelentrysnapshot",
            name="track",
            field=models.ManyToManyField(to="panels.TrackRecord"),
        ),
        migrations.AddField(
            model_name="activity",
            name="panel",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="panels.GenePanel"
            ),
        ),
        migrations.AddField(
            model_name="activity",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
