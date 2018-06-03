# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0011_auto_20141013_1517'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='specialization',
            field=models.PositiveIntegerField(verbose_name='Специализация', choices=[(1, 'Только Python'), (2, 'Есть секция/отделение про Python'), (3, 'Есть упоминания про Python')], default=1),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='contacts',
            field=models.CharField(help_text='Контактные лица через запятую, координирующие/устраивающие событие.<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].', verbose_name='Контактные лица', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='place',
            field=models.ForeignKey(help_text='Укажите место проведения мероприятия.<br><b>Конкретный адрес следует указывать в описании.</b><br>Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».', blank=True, null=True, related_name='events', on_delete=models.CASCADE, verbose_name='Место', to='apps.Place'),
        ),
    ]
