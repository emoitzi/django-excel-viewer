# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0005_create_editor_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemporaryDocument',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('file', models.FileField(upload_to='')),
            ],
        ),
        migrations.AlterField(
            model_name='changerequest',
            name='status',
            field=models.IntegerField(default=1, choices=[(1, 'Pending'), (2, 'Accepted'), (3, 'Declined'), (4, 'Revoked')]),
        ),
    ]
