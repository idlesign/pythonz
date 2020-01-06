# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0027_auto_20151104_0511'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_public',
            field=models.BooleanField(db_index=True, default=True, verbose_name='Публичный профиль', help_text='Если выключить, то увидеть ваш профиль сможете только вы.<br>В списках пользователей профиль значиться тоже не будет.'),
        ),
    ]
