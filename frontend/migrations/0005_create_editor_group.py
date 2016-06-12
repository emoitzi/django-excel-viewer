# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def create_editor_group(apps, schema):
    Group = apps.get_model("auth", "Group")
    group, _ = Group.objects.get_or_create(name="editor")


def noop(apps, schema):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0004_auto_20160612_1616'),
    ]

    operations = [
        migrations.RunPython(create_editor_group, noop)
    ]
