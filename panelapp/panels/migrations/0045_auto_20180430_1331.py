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
# Generated by Django 1.11.6 on 2018-04-30 12:31
from __future__ import unicode_literals

import django.contrib.postgres.fields.ranges
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0044_auto_20180326_1616'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='str',
            name='normal_range',
        ),
        migrations.RemoveField(
            model_name='str',
            name='pathogenic_range',
        ),
        migrations.RemoveField(
            model_name='str',
            name='prepathogenic_range',
        ),
        migrations.AddField(
            model_name='str',
            name='chromosome',
            field=models.CharField(choices=[('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'), ('21', '21'), ('22', '22'), ('X', 'X'), ('Y', 'Y')], default='1', help_text='Chromosome', max_length=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='str',
            name='normal_repeats',
            field=models.IntegerField(default=1, help_text='=< Maximum normal number of repeats', verbose_name='Normal'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='str',
            name='pathogenic_repeats',
            field=models.IntegerField(default=1, help_text='>= Minimum fully penetrant pathogenic number of repeats', verbose_name='Pathogenic'),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='str',
            name='position_37'
        ),
        migrations.AddField(
            model_name='str',
            name='position_37',
            field=django.contrib.postgres.fields.ranges.IntegerRangeField(default=(1, 1)),
        ),
        migrations.RemoveField(
            model_name='str',
            name='position_38'
        ),
        migrations.AddField(
            model_name='str',
            name='position_38',
            field=django.contrib.postgres.fields.ranges.IntegerRangeField(default=(1, 1)),
        ),
        migrations.AlterField(
            model_name='trackrecord',
            name='issue_type',
            field=models.CharField(choices=[('Created', 'Created'), ('NewSource', 'Added New Source'), ('RemovedSource', 'Removed Source'), ('ChangedGeneName', 'Changed Gene Name'), ('SetPhenotypes', 'Set Phenotypes'), ('SetModelofInheritance', 'Set Model of Inheritance'), ('ClearSources', 'Clear Sources'), ('SetModeofPathogenicity', 'Set mode of pathogenicity'), ('GeneClassifiedbyGenomicsEnglandCurator', 'Gene classified by Genomics England curator'), ('EntityClassifiedbyGenomicsEnglandCurator', 'Entity classified by Genomics England curator'), ('SetModeofInheritance', 'Set mode of inheritance'), ('SetPenetrance', 'Set penetrance'), ('SetPublications', 'Set publications'), ('ApprovedGene', 'Approved Gene'), ('ApprovedEntity', 'Approved Entity'), ('GelStatusUpdate', 'Gel Status Update'), ('UploadGeneInformation', 'Upload gene information'), ('RemovedTag', 'Removed Tag'), ('AddedTag', 'Added Tag'), ('ChangedSTRName', 'Changed STR Name'), ('ChangedChromosome', 'Changed Chromosome'), ('ChangedPosition37', 'Changed GRCh37'), ('ChangedPosition38', 'Changed GRCh38'), ('ChangedNormalRange', 'Changed Normal Range'), ('ChangedPrepathogenicRange', 'Changed Pre-Pathogenic Range'), ('ChangedPathogenicRange', 'Changed Pathogenic Range'), ('RemovedGene', 'Removed Gene from the STR'), ('ChangedRepeatedSequence', 'Changed Repeated Sequence')], max_length=512),
        ),
    ]
