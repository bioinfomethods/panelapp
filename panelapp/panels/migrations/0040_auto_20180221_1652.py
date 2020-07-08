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
# Generated by Django 1.11.6 on 2018-02-21 16:52
from __future__ import unicode_literals

from django.db import (
    migrations,
    models,
)


class Migration(migrations.Migration):

    dependencies = [("panels", "0039_auto_20180221_1347")]

    operations = [
        migrations.AddField(
            model_name="str",
            name="repeated_sequence",
            field=models.CharField(default="ATAT", max_length=128),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="trackrecord",
            name="issue_type",
            field=models.CharField(
                choices=[
                    ("Created", "Created"),
                    ("NewSource", "Added New Source"),
                    ("RemovedSource", "Removed Source"),
                    ("ChangedGeneName", "Changed Gene Name"),
                    ("SetPhenotypes", "Set Phenotypes"),
                    ("SetModelofInheritance", "Set Model of Inheritance"),
                    ("ClearSources", "Clear Sources"),
                    ("SetModeofPathogenicity", "Set mode of pathogenicity"),
                    (
                        "GeneClassifiedbyGenomicsEnglandCurator",
                        "Gene classified by Genomics England curator",
                    ),
                    (
                        "EntityClassifiedbyGenomicsEnglandCurator",
                        "Entity classified by Genomics England curator",
                    ),
                    ("SetModeofInheritance", "Set mode of inheritance"),
                    ("SetPenetrance", "Set penetrance"),
                    ("SetPublications", "Set publications"),
                    ("ApprovedGene", "Approved Gene"),
                    ("ApprovedEntity", "Approved Entity"),
                    ("GelStatusUpdate", "Gel Status Update"),
                    ("UploadGeneInformation", "Upload gene information"),
                    ("RemovedTag", "Removed Tag"),
                    ("AddedTag", "Added Tag"),
                    ("ChangedSTRName", "Changed STR Name"),
                    ("ChangedNormalRange", "Changed Normal Range"),
                    ("ChangedPrepathogenicRange", "Changed Pre-Pathogenic Range"),
                    ("ChangedPathogenicRange", "Changed Pathogenic Range"),
                    ("RemovedGene", "Removed Gene from the STR"),
                ],
                max_length=512,
            ),
        ),
    ]
