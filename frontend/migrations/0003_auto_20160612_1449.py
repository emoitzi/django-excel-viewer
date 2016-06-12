# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0002_create_user_group'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='changerequest',
            options={'ordering': ['created_on']},
        ),
    ]
