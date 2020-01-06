# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0002_user_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='place',
            name='geo_title',
            field=models.TextField(blank=True, null=True, unique=True, verbose_name='Полное название'),
        ),
        migrations.AlterField(
            model_name='user',
            name='place',
            field=models.ForeignKey(blank=True, null=True, to='apps.Place', verbose_name='Место', help_text='Место вашего пребывания (страна, город, село). Например: Россия, Новосибирск.', related_name='users', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='user',
            name='timezone',
            field=models.CharField(max_length=150, blank=True, null=True, verbose_name='Часовой пояс', help_text='Название часового пояса. Например: Asia/Novosibirsk.<br>* Устанавливается автоматически в зависимости от места пребывания (см. выше).'),
        ),
    ]
