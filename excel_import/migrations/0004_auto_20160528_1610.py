# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('excel_import', '0003_document_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cell',
            name='coordinate',
            field=models.CharField(max_length=15),
        ),
    ]
