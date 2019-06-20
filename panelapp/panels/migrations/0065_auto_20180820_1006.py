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
# Generated by Django 2.0.8 on 2018-08-20 10:06

import django.contrib.postgres.fields.ranges
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("panels", "0064_auto_20180724_1334")]

    operations = [
        migrations.RemoveIndex(
            model_name="evaluation", name="panels_eval_user_id_7e6977_idx"
        ),
        migrations.RemoveIndex(
            model_name="genepanelentrysnapshot", name="panels_gene_panel_i_d90d44_idx"
        ),
        migrations.RemoveIndex(
            model_name="genepanelentrysnapshot", name="panels_gene_gene_co_9223b2_idx"
        ),
        migrations.RemoveIndex(
            model_name="genepanelsnapshot", name="panels_gene_panel_i_2a8178_idx"
        ),
        migrations.RemoveIndex(
            model_name="evidence", name="panels_evid_reviewe_31dac4_idx"
        ),
        migrations.RemoveIndex(model_name="str", name="panels_str_panel_i_68b388_idx"),
        migrations.RemoveIndex(model_name="str", name="panels_str_gene_co_bad503_idx"),
        migrations.RemoveIndex(
            model_name="region", name="panels_regi_panel_i_35b205_idx"
        ),
        migrations.RemoveIndex(
            model_name="region", name="panels_regi_gene_co_0c95f6_idx"
        ),
        migrations.AlterField(
            model_name="genepanelentrysnapshot",
            name="type_of_variants",
            field=models.CharField(
                choices=[
                    ("small", "Small variants"),
                    ("cnv_loss", "CNV Loss"),
                    ("cnv_gain", "CNV Gain"),
                    ("cnv_both", "CNV Both gain and loss"),
                ],
                default="small",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="region",
            name="position_37",
            field=django.contrib.postgres.fields.ranges.IntegerRangeField(
                blank=True, null=True
            ),
        ),
        migrations.AlterField(
            model_name="region",
            name="type_of_variants",
            field=models.CharField(
                choices=[
                    ("small", "Small variants"),
                    ("cnv_loss", "CNV Loss"),
                    ("cnv_gain", "CNV Gain"),
                    ("cnv_both", "CNV Both gain and loss"),
                ],
                default="small",
                max_length=32,
                verbose_name="Variation type",
            ),
        ),
        migrations.AlterField(
            model_name="str",
            name="position_37",
            field=django.contrib.postgres.fields.ranges.IntegerRangeField(
                blank=True, null=True
            ),
        ),
    ]
