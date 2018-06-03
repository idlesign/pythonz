# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0025_auto_20150625_1720'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_created', models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)),
                ('time_published', models.DateTimeField(editable=False, verbose_name='Дата публикации', null=True)),
                ('time_modified', models.DateTimeField(editable=False, verbose_name='Дата редактирования', null=True)),
                ('status', models.PositiveIntegerField(default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')], verbose_name='Статус')),
                ('supporters_num', models.PositiveIntegerField(default=0, verbose_name='Поддержка')),
                ('src_alias', models.CharField(max_length=20, choices=[('pydigest', 'pythondigest.ru')], verbose_name='Идентификатор источника')),
                ('realm_name', models.CharField(max_length=20, verbose_name='Идентификатор области на pythonz')),
                ('url', models.URLField(unique=True, verbose_name='Страница ресурса')),
                ('title', models.CharField(max_length=255, verbose_name='Название')),
                ('description', models.TextField(default='', verbose_name='Описание', blank=True)),
                ('last_editor', models.ForeignKey(help_text='Пользователь, последним отредактировавший объект.', related_name='externalresource_editors', on_delete=models.CASCADE, verbose_name='Редактор', to=settings.AUTH_USER_MODEL, blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Внешние ресурсы',
                'verbose_name': 'Внешний ресурс',
            },
        ),
        migrations.AlterField(
            model_name='article',
            name='source',
            field=models.PositiveIntegerField(default=1, verbose_name='Тип источника', choices=[(1, 'Написана на этом сайте'), (2, 'Соскоблена с другого сайта')], help_text='Указывает на механизм, при помощи которого статья появилась на сайте.'),
        ),
        migrations.AlterField(
            model_name='book',
            name='description',
            field=models.TextField(verbose_name='Описание', help_text='Аннотация к книге, или другое краткое описание. <strong>Без обозначения личного отношения. Личное отношение можно выразить в Обсуждениях к материалу.</strong>'),
        ),
        migrations.AlterField(
            model_name='community',
            name='description',
            field=models.TextField(verbose_name='Описание', help_text='Сжатая предварительная информация о сообществе (например, направление деятельности). <strong>Без обозначения личного отношения. Личное отношение можно выразить в Обсуждениях к материалу.</strong>'),
        ),
        migrations.AlterField(
            model_name='community',
            name='text_src',
            field=models.TextField(verbose_name='Исходный текст', help_text='<strong>Без обозначения личного отношения. Личное отношение можно выразить в Обсуждениях к материалу.</strong>'),
        ),
        migrations.AlterField(
            model_name='event',
            name='description',
            field=models.TextField(verbose_name='Описание', help_text='Краткое описание события. <strong>Без обозначения личного отношения. Личное отношение можно выразить в Обсуждениях к материалу.</strong>'),
        ),
        migrations.AlterField(
            model_name='event',
            name='text_src',
            field=models.TextField(verbose_name='Исходный текст', help_text='<strong>Без обозначения личного отношения. Личное отношение можно выразить в Обсуждениях к материалу.</strong>'),
        ),
        migrations.AlterField(
            model_name='historicalarticle',
            name='source',
            field=models.PositiveIntegerField(default=1, verbose_name='Тип источника', choices=[(1, 'Написана на этом сайте'), (2, 'Соскоблена с другого сайта')], help_text='Указывает на механизм, при помощи которого статья появилась на сайте.'),
        ),
        migrations.AlterField(
            model_name='reference',
            name='title',
            field=models.CharField(verbose_name='Название', unique=True, max_length=255, help_text='Здесь следует указать название раздела справки или пакета, модуля, класса, метода, функции и т.п.'),
        ),
        migrations.AlterField(
            model_name='version',
            name='text_src',
            field=models.TextField(verbose_name='Исходный текст', help_text=('Обзорное, более полное описание нововведений и изменений, произошедших в версии. <strong>Без обозначения личного отношения. Личное отношение можно выразить в Обсуждениях к материалу.</strong>',)),
        ),
        migrations.AlterField(
            model_name='video',
            name='description',
            field=models.TextField(verbose_name='Описание', help_text='Краткое описание того, о чём это видео. <strong>Без обозначения личного отношения. Личное отношение можно выразить в Обсуждениях к материалу.</strong>'),
        ),
    ]
