# Generated by Django 2.1.3 on 2019-04-24 15:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0070_historicalsnapshot'),
    ]

    operations = [
        migrations.AlterField(
            model_name='genepanelentrysnapshot',
            name='panel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='panels.GenePanelSnapshot'),
        ),
        migrations.AlterField(
            model_name='genepanelsnapshot',
            name='level4title',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='panels.Level4Title'),
        ),
        migrations.AlterField(
            model_name='genepanelsnapshot',
            name='panel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='panels.GenePanel'),
        ),
        migrations.AlterField(
            model_name='region',
            name='panel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='panels.GenePanelSnapshot'),
        ),
        migrations.AlterField(
            model_name='str',
            name='panel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='panels.GenePanelSnapshot'),
        ),
    ]
