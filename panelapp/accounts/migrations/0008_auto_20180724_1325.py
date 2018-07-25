# Generated by Django 2.0.6 on 2018-07-24 12:25

from django.db import migrations
from panels.models import PanelType


user_support_group = 'User Support'
site_editor_group = 'Site Editor'
file_upload_curation_group = 'File Upload Curation'


def add_paneltype_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    paneltype_content_type = ContentType.objects.get_for_model(PanelType)
    site_editor = Group.objects.get(name=site_editor_group)
    site_editor.permissions.set(
        Permission.objects.filter(content_type=paneltype_content_type)
    )


def remove_paneltype_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    paneltype_content_type = ContentType.objects.get_for_model(PanelType)
    try:
        site_editor = Group.objects.get(name=site_editor_group)
        site_editor.permissions.remove(
            Permission.objects.filter(content_type=paneltype_content_type)
        )
    except Group.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_auto_20180615_1147'),
    ]

    operations = [
        migrations.RunPython(add_paneltype_permissions, remove_paneltype_permissions)
    ]
