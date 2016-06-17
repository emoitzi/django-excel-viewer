# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('excel_import', '0009_auto_20160612_1323'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cell',
            name='color_name',
            field=models.CharField(max_length=20, blank=True),
        ),
        migrations.AlterField(
            model_name='documentcolors',
            name='name',
            field=models.CharField(max_length=20, db_index=True),
        ),
    ]
