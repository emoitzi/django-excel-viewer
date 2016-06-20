# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('excel_import', '0005_auto_20160529_1128'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2016, 5, 29, 12, 1, 38, 762519, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='document',
            name='replaces',
            field=models.ForeignKey(to='excel_import.Document', null=True, blank=True),
        ),
    ]
