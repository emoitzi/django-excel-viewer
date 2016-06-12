# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('excel_import', '0008_document_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cell',
            name='document',
            field=models.ForeignKey(to='excel_import.Document'),
        ),
    ]
