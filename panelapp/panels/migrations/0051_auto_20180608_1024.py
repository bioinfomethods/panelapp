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
# Generated by Django 1.11.6 on 2018-06-08 09:24
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import Q


def migrate_other_value(apps, schema_editor):
    # Migrate `Other` value stored in database as it's stored with a comment
    Evaluation = apps.get_model("panels", "Evaluation")
    for ev in Evaluation.objects.filter(
        Q(moi="Other - please specifiy in evaluation comments")
        | Q(mode_of_pathogenicity="Other - please provide details in the comments")
    ):
        if ev.moi == "Other - please specifiy in evaluation comments":
            ev.moi = "Other"
        if ev.mode_of_pathogenicity == "Other - please provide details in the comments":
            ev.mode_of_pathogenicity = "Other"
        ev.save()


def migrate_other_back(apps, schema_editor):
    Evaluation = apps.get_model("panels", "Evaluation")
    for ev in Evaluation.objects.filter(
        Q(moi="Other") | Q(mode_of_pathogenicity="Other")
    ):
        if ev.moi == "Other":
            ev.moi = "Other - please specifiy in evaluation comments"
        if ev.mode_of_pathogenicity == "Other":
            ev.mode_of_pathogenicity = "Other - please provide details in the comments"
        ev.save()


class Migration(migrations.Migration):

    dependencies = [("panels", "0050_auto_20180607_1545")]

    operations = [migrations.RunPython(migrate_other_value, migrate_other_back)]
