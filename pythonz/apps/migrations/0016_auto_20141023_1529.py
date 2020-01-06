# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0015_auto_20141023_1500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discussion',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True, blank=True, verbose_name='Тип содержимого', related_name='discussion_discussions', on_delete=models.CASCADE),
        ),
    ]
