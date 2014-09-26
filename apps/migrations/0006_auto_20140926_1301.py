# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0005_place_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='place',
            name='description',
            field=models.TextField(verbose_name='Описание', blank=True, default=''),
        ),
    ]
