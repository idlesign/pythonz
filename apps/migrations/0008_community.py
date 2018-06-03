# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import apps.generics.models
from django.conf import settings
import etc.models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0007_auto_20141004_1034'),
    ]

    operations = [
        migrations.CreateModel(
            name='Community',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('text', models.TextField(verbose_name='Текст')),
                ('text_src', models.TextField(verbose_name='Исходный текст')),
                ('title', models.CharField(verbose_name='Название', max_length=255, unique=True)),
                ('description', models.TextField(verbose_name='Описание', help_text='Пара-тройка предложений, описывающих, о чём пойдёт речь в статье.')),
                ('cover', models.ImageField(null=True, verbose_name='Обложка', upload_to=apps.generics.models.get_upload_to, max_length=255, blank=True)),
                ('year', models.CharField(null=True, verbose_name='Год', max_length=10, blank=True)),
                ('time_created', models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)),
                ('time_published', models.DateTimeField(null=True, verbose_name='Дата публикации', editable=False)),
                ('time_modified', models.DateTimeField(null=True, verbose_name='Дата редактирования', editable=False)),
                ('status', models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')])),
                ('supporters_num', models.PositiveIntegerField(verbose_name='Количество поддержавших', default=0)),
                ('url', models.URLField(null=True, verbose_name='Страница в сети', blank=True)),
                ('contacts', models.CharField(verbose_name='Контактное лицо', help_text='Контактные лица, представляющие сообщество, координаторы, основатели.<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].', max_length=255)),
                ('linked', models.ManyToManyField(verbose_name='Связанные объекты', help_text='Выберите объекты, имеющие отношение к данному.', to='apps.Community', blank=True, related_name='linked_rel_+')),
                ('place', models.ForeignKey(to='apps.Place', verbose_name='Место', related_name='communities', on_delete=models.CASCADE, null=True, help_text='Для географически локализованных сообществ можно указать место (страна, город, село).<br>Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».', blank=True)),
                ('submitter', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='community_submitters', on_delete=models.CASCADE, verbose_name='Добавил')),
            ],
            options={
                'verbose_name': 'Сообщество',
                'verbose_name_plural': 'Сообщества',
            },
            bases=(etc.models.InheritedModel, models.Model),
        ),
    ]
