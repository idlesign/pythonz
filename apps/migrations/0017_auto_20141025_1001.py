# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0016_auto_20141023_1529'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='discussion',
            unique_together=None,
        ),
    ]
