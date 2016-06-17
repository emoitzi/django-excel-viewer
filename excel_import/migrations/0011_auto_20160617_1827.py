# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('excel_import', '0010_auto_20160617_1439'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentcolors',
            name='color',
            field=models.CharField(max_length=8),
        ),
    ]
