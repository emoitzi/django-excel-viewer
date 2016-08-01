# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('excel_import', '0011_auto_20160617_1827'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='worksheet',
            field=models.IntegerField(default=0),
        ),
    ]
