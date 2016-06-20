# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('excel_import', '0007_document_current'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='status',
            field=models.IntegerField(default=1, choices=[(1, 'Open'), (2, 'Semi locked'), (3, 'Locked')]),
        ),
    ]
