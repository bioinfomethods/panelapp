# Generated by Django 2.1.9 on 2019-07-10 08:11

from django.db import (
    migrations,
    models,
)


class Migration(migrations.Migration):

    dependencies = [
        ("panels", "0072_merge_20190522_1553"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicalsnapshot",
            name="reason",
            field=models.TextField(null=True),
        ),
    ]
