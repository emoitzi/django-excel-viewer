# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def create_user_group(apps, schema):
    Group = apps.get_model("auth", "Group")
    group, _ = Group.objects.get_or_create(name="user")


def noop(apps, schema):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_user_group, noop)
    ]
