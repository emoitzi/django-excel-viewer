# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('excel_import', '0004_auto_20160528_1610'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='row',
            name='document',
        ),
        migrations.AlterModelOptions(
            name='cell',
            options={'ordering': ['id']},
        ),
        migrations.RemoveField(
            model_name='cell',
            name='row',
        ),
        migrations.AddField(
            model_name='cell',
            name='document',
            field=models.ForeignKey(to='excel_import.Document', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='cell',
            name='first_cell',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='cell',
            name='last_cell',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='Row',
        ),
    ]
