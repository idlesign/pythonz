# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import etc.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('apps', '0013_event_fee'),
    ]

    operations = [
        migrations.CreateModel(
            name='Discussion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(verbose_name='Текст')),
                ('text_src', models.TextField(verbose_name='Исходный текст')),
                ('time_created', models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)),
                ('time_published', models.DateTimeField(verbose_name='Дата публикации', editable=False, null=True)),
                ('time_modified', models.DateTimeField(verbose_name='Дата редактирования', editable=False, null=True)),
                ('status', models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')])),
                ('supporters_num', models.PositiveIntegerField(verbose_name='Поддержка', default=0)),
                ('object_id', models.PositiveIntegerField(verbose_name='ID объекта', db_index=True)),
                ('content_type', models.ForeignKey(verbose_name='Тип содержимого', related_name='discussion_opinions', on_delete=models.CASCADE, to='contenttypes.ContentType')),
                ('last_editor', models.ForeignKey(verbose_name='Редактор', help_text='Пользователь, последним отредактировавший объект.', related_name='discussion_editors', on_delete=models.CASCADE, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('submitter', models.ForeignKey(verbose_name='Автор', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Мнение',
                'verbose_name_plural': 'Мнения',
            },
            bases=(etc.models.InheritedModel, models.Model),
        ),
        migrations.AlterUniqueTogether(
            name='opinion',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='opinion',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='opinion',
            name='last_editor',
        ),
        migrations.RemoveField(
            model_name='opinion',
            name='submitter',
        ),
        migrations.DeleteModel(
            name='Opinion',
        ),
        migrations.AlterUniqueTogether(
            name='discussion',
            unique_together=set([('content_type', 'object_id', 'submitter')]),
        ),
        migrations.AlterField(
            model_name='article',
            name='supporters_num',
            field=models.PositiveIntegerField(verbose_name='Поддержка', default=0),
        ),
        migrations.AlterField(
            model_name='book',
            name='description',
            field=models.TextField(verbose_name='Описание', help_text='Аннотация к книге, или другое краткое описание. <strong>Без обозначения личного отношения. Личное отношение можно выразить во Мнениях.</strong>'),
        ),
        migrations.AlterField(
            model_name='book',
            name='supporters_num',
            field=models.PositiveIntegerField(verbose_name='Поддержка', default=0),
        ),
        migrations.AlterField(
            model_name='community',
            name='description',
            field=models.TextField(verbose_name='Описание', help_text='Сжатая предварительная информация о сообществе (например, направление деятельности). <strong>Без обозначения личного отношения. Личное отношение можно выразить во Мнениях.</strong>'),
        ),
        migrations.AlterField(
            model_name='community',
            name='supporters_num',
            field=models.PositiveIntegerField(verbose_name='Поддержка', default=0),
        ),
        migrations.AlterField(
            model_name='community',
            name='text_src',
            field=models.TextField(verbose_name='Исходный текст', help_text='<strong>Без обозначения личного отношения. Личное отношение можно выразить во Мнениях.</strong>'),
        ),
        migrations.AlterField(
            model_name='event',
            name='description',
            field=models.TextField(verbose_name='Описание', help_text='Краткое описание события. <strong>Без обозначения личного отношения. Личное отношение можно выразить во Мнениях.</strong>'),
        ),
        migrations.AlterField(
            model_name='event',
            name='supporters_num',
            field=models.PositiveIntegerField(verbose_name='Поддержка', default=0),
        ),
        migrations.AlterField(
            model_name='event',
            name='text_src',
            field=models.TextField(verbose_name='Исходный текст', help_text='<strong>Без обозначения личного отношения. Личное отношение можно выразить во Мнениях.</strong>'),
        ),
        migrations.AlterField(
            model_name='event',
            name='time_finish',
            field=models.DateTimeField(verbose_name='Завершение', blank=True, help_text='Дату завершения можно и не указывать.', null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='type',
            field=models.PositiveIntegerField(verbose_name='Тип', default=1, choices=[(1, 'Встреча'), (3, 'Лекция'), (2, 'Конференция'), (4, 'Спринт')]),
        ),
        migrations.AlterField(
            model_name='place',
            name='supporters_num',
            field=models.PositiveIntegerField(verbose_name='Поддержка', default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='email_public',
            field=models.EmailField(verbose_name='Эл. почта', blank=True, help_text='Адрес электронной почты для показа посетителям сайта.', null=True, max_length=75),
        ),
        migrations.AlterField(
            model_name='user',
            name='supporters_num',
            field=models.PositiveIntegerField(verbose_name='Поддержка', default=0),
        ),
        migrations.AlterField(
            model_name='video',
            name='description',
            field=models.TextField(verbose_name='Описание', help_text='Краткое описание того, о чём это видео. <strong>Без обозначения личного отношения. Личное отношение можно выразить во Мнениях.</strong>'),
        ),
        migrations.AlterField(
            model_name='video',
            name='supporters_num',
            field=models.PositiveIntegerField(verbose_name='Поддержка', default=0),
        ),
    ]
