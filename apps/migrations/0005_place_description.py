# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0004_auto_20140926_0808'),
    ]

    operations = [
        migrations.AddField(
            model_name='place',
            name='description',
            field=models.TextField(blank=True, verbose_name='Описание', null=True),
            preserve_default=True,
        ),
    ]
