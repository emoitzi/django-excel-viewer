# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0003_auto_20160612_1449'),
    ]

    operations = [
        migrations.RenameField(
            model_name='changerequest',
            old_name='accepted_by',
            new_name='reviewed_by',
        ),
        migrations.RenameField(
            model_name='changerequest',
            old_name='accepted_on',
            new_name='reviewed_on',
        ),
        migrations.AddField(
            model_name='changerequest',
            name='status',
            field=models.IntegerField(default=1, choices=[(1, 'Pending'), (2, 'Accepted'), (3, 'Declined')]),
        ),
    ]
