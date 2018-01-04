# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-07 11:09
from __future__ import unicode_literals

from django.db import migrations


def combine_statuses(apps, schema_editor):
    GenePanel = apps.get_model('panels', 'GenePanel')
    for gp in GenePanel.objects.all():
        if gp.deleted:
            gp.status = 'deleted'
        elif gp.promoted:
            gp.status = 'promoted'
        elif gp.approved:
            gp.status = 'public'
        else:
            gp.status = 'internal'
        gp.save()


def separate_statuses(apps, schema_editor):
    GenePanel = apps.get_model('panels', 'GenePanel')
    for gp in GenePanel.objects.all():
        if gp.status == 'deleted':
            gp.deleted = True
        if gp.status == 'promoted':
            gp.promoted = True
        if gp.status == 'public' or gp.status == 'promoted':
            gp.approved = True

        gp.save()


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0032_genepanel_status'),
    ]

    operations = [
        migrations.RunPython(combine_statuses, separate_statuses)
    ]
