# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0009_auto_20141004_1314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='community',
            name='contacts',
            field=models.CharField(blank=True, max_length=255, verbose_name='Контактные лица', null=True, help_text='Контактные лица через запятую, представляющие сообщество, координаторы, основатели.<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].'),
        ),
    ]
