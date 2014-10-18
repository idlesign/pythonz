# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0012_auto_20141018_1416'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='fee',
            field=models.BooleanField(verbose_name='Участие платное', default=False, db_index=True),
            preserve_default=True,
        ),
    ]
