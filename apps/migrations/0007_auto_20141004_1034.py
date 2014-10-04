# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0006_auto_20140926_1301'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_public',
            field=models.EmailField(verbose_name='Почта', max_length=75, blank=True, help_text='Адрес электронной почты для показа посетителям сайта.', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='url',
            field=models.URLField(verbose_name='Страница в сети', blank=True, null=True),
            preserve_default=True,
        ),
    ]
