# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0010_auto_20141004_1519'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventdetails',
            name='place',
        ),
        migrations.RemoveField(
            model_name='event',
            name='details',
        ),
        migrations.DeleteModel(
            name='EventDetails',
        ),
        migrations.AddField(
            model_name='event',
            name='contacts',
            field=models.CharField(help_text='Контактные лица через запятую, представляющие сообщество, координаторы, основатели.<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].', blank=True, null=True, verbose_name='Контактные лица', max_length=255),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='place',
            field=models.ForeignKey(verbose_name='Место', to='apps.Place', help_text='Укажите место проведения мероприятия. <b>Конкретный адрес следует указывать в описании.</b><br>Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».', blank=True, null=True, related_name='events', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='time_finish',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Завершение'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='time_start',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Начало'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='url',
            field=models.URLField(blank=True, null=True, verbose_name='Страница в сети'),
            preserve_default=True,
        ),
    ]
