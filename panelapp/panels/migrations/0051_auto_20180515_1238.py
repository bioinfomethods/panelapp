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
# Generated by Django 1.11.6 on 2018-05-15 11:38
from __future__ import unicode_literals

import array_field_select.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0050_auto_20180514_1622'),
    ]

    operations = [
        migrations.AlterField(
            model_name='region',
            name='type_of_effects',
            field=array_field_select.fields.ArrayField(base_field=models.CharField(choices=[('transcript_ablation', 'A feature ablation whereby the deleted region includes a transcript feature'), ('splice_acceptor_variant', "A splice variant that changes the 2 base region at the 3' end of an intron"), ('splice_donor_variant', "A splice variant that changes the 2 base region at the 5' end of an intron"), ('stop_gained', 'A sequence variant whereby at least one base of a codon is changed, resulting in a premature stop codon, leading to a shortened transcript'), ('frameshift_variant', 'A sequence variant which causes a disruption of the translational reading frame, because the number of nucleotides inserted or deleted is not a multiple of three'), ('stop_lost', 'A sequence variant where at least one base of the terminator codon (stop) is changed, resulting in an elongated transcript'), ('start_lost', 'A codon variant that changes at least one base of the canonical start codon'), ('transcript_amplification', 'A feature amplification of a region containing a transcript'), ('inframe_insertion', 'An inframe non synonymous variant that inserts bases into in the coding sequence'), ('inframe_deletion', 'An inframe non synonymous variant that deletes bases from the coding sequence'), ('missense_variant', 'A sequence variant, that changes one or more bases, resulting in a different amino acid sequence but where the length is preserved'), ('protein_altering_variant', 'A sequence_variant which is predicted to change the protein encoded in the coding sequence'), ('splice_region_variant', 'A sequence variant in which a change has occurred within the region of the splice site, either within 1-3 bases of the exon or 3-8 bases of the intron'), ('incomplete_terminal_codon_variant', 'A sequence variant where at least one base of the final codon of an incompletely annotated transcript is changed'), ('start_retained_variant', 'A sequence variant where at least one base in the start codon is changed, but the start remains'), ('stop_retained_variant', 'A sequence variant where at least one base in the terminator codon is changed, but the terminator remains'), ('synonymous_variant', 'A sequence variant where there is no resulting change to the encoded amino acid'), ('coding_sequence_variant', 'A sequence variant that changes the coding sequence'), ('mature_miRNA_variant', 'A transcript variant located with the sequence of the mature miRNA'), ('5_prime_UTR_variant', "A UTR variant of the 5' UTR"), ('3_prime_UTR_variant', "A UTR variant of the 3' UTR"), ('non_coding_transcript_exon_variant', 'A sequence variant that changes non-coding exon sequence in a non-coding transcript'), ('intron_variant', 'A transcript variant occurring within an intron'), ('NMD_transcript_variant', 'A variant in a transcript that is the target of NMD'), ('non_coding_transcript_variant', 'A transcript variant of a non coding RNA gene'), ('upstream_gene_variant', "A sequence variant located 5' of a gene"), ('downstream_gene_variant', "A sequence variant located 3' of a gene"), ('TFBS_ablation', 'A feature ablation whereby the deleted region includes a transcription factor binding site'), ('TFBS_amplification', 'A feature amplification of a region containing a transcription factor binding site'), ('TF_binding_site_variant', 'A sequence variant located within a transcription factor binding site'), ('regulatory_region_ablation', 'A feature ablation whereby the deleted region includes a regulatory region'), ('regulatory_region_amplification', 'A feature amplification of a region containing a regulatory region'), ('feature_elongation', 'A sequence variant that causes the extension of a genomic feature, with regard to the reference sequence'), ('regulatory_region_variant', 'A sequence variant located within a regulatory region'), ('feature_truncation', 'A sequence variant that causes the reduction of a genomic feature, with regard to the reference sequence'), ('intergenic_variant', 'A sequence variant located in the intergenic region, between genes')], max_length=32), help_text='Press CTRL or CMD button to select multiple effects', size=None),
        ),
        migrations.AlterField(
            model_name='region',
            name='type_of_variants',
            field=models.CharField(choices=[('Small', 'Small'), ('SV', 'SV'), ('CNV', 'CNV')], max_length=128),
        ),
    ]
