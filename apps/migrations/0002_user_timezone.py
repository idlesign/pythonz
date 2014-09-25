# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='timezone',
            field=models.CharField(help_text='Название часового пояса. Например: Asia/Novosibirsk.', null=True, verbose_name='Часовой пояс', max_length=150, blank=True),
            preserve_default=True,
        ),
    ]
