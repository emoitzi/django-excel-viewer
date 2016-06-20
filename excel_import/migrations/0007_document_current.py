# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('excel_import', '0006_auto_20160529_1201'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='current',
            field=models.BooleanField(default=True),
        ),
    ]
