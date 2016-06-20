# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('excel_import', '0007_document_current'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChangeRequest',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('new_value', models.CharField(max_length=255)),
                ('old_value', models.CharField(max_length=255, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('accepted_on', models.DateTimeField(null=True, blank=True)),
                ('accepted_by', models.ForeignKey(null=True, related_name='+', blank=True, to=settings.AUTH_USER_MODEL)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('target_cell', models.ForeignKey(to='excel_import.Cell')),
            ],
        ),
    ]
