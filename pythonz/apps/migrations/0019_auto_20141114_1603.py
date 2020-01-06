# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0018_auto_20141108_1538'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalReference',
            fields=[
                ('id', models.IntegerField(blank=True, db_index=True, auto_created=True, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Текст')),
                ('text_src', models.TextField(verbose_name='Исходный текст')),
                ('title', models.CharField(db_index=True, max_length=255, verbose_name='Название')),
                ('description', models.TextField(verbose_name='Описание')),
                ('submitter_id', models.IntegerField(blank=True, null=True, db_index=True, verbose_name='Добавил')),
                ('cover', models.TextField(blank=True, null=True, max_length=255, verbose_name='Обложка')),
                ('year', models.CharField(blank=True, null=True, max_length=10, verbose_name='Год')),
                ('time_created', models.DateTimeField(blank=True, editable=False, verbose_name='Дата создания')),
                ('time_published', models.DateTimeField(null=True, editable=False, verbose_name='Дата публикации')),
                ('time_modified', models.DateTimeField(null=True, editable=False, verbose_name='Дата редактирования')),
                ('status', models.PositiveIntegerField(choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')], default=1, verbose_name='Статус')),
                ('supporters_num', models.PositiveIntegerField(default=0, verbose_name='Поддержка')),
                ('last_editor_id', models.IntegerField(help_text='Пользователь, последним отредактировавший объект.', blank=True, db_index=True, null=True, verbose_name='Редактор')),
                ('type', models.PositiveIntegerField(help_text='Служит для структурирования информации. Справочные статьи разных типов могут выглядеть по-разному.', choices=[(1, 'Раздел справки'), (2, 'Описание пакета'), (3, 'Описание модуля'), (4, 'Описание функции'), (5, 'Описание класса или типа'), (6, 'Описание метода класса или типа')], default=1, verbose_name='Тип статьи')),
                ('parent_id', models.IntegerField(help_text='Укажите родительский раздел. Например, для модуля можно указать раздел справки, в которому он относится; для метода &#8212; класс.', blank=True, db_index=True, null=True, verbose_name='Родитель')),
                ('version_added_id', models.IntegerField(help_text='Версия Python, для которой впервые стала актульна данная статья<br>(версия, где впервые появился модуль, пакет, класс, функция).', blank=True, db_index=True, null=True, verbose_name='Добавлено в')),
                ('version_deprecated_id', models.IntegerField(help_text='Версия Python, для которой впервые данная статья перестала быть актуальной<br>(версия, где модуль, пакет, класс, функция были объявлены устаревшими).', blank=True, db_index=True, null=True, verbose_name='Устарело в')),
                ('func_proto', models.CharField(help_text='Для функций/методов. Описание интерфейса, например: <i>my_func(arg, kwarg=None)</i>', blank=True, max_length=250, null=True, verbose_name='Прототип')),
                ('func_params', models.TextField(help_text='Для функций/методов. Описание параметров функции.', blank=True, null=True, verbose_name='Параметры')),
                ('func_result', models.CharField(help_text='Для функций/методов. Описание результата, например: <i>int</i>.', blank=True, max_length=250, null=True, verbose_name='Результат')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'verbose_name': 'historical Статья справочника',
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='reference',
            options={'ordering': ('parent_id', 'title'), 'verbose_name_plural': 'Справочник', 'verbose_name': 'Статья справочника'},
        ),
        migrations.AlterModelOptions(
            name='version',
            options={'ordering': ('title',), 'verbose_name_plural': 'Версии Python', 'verbose_name': 'Версия Python'},
        ),
        migrations.AlterField(
            model_name='reference',
            name='description',
            field=models.TextField(help_text='Краткое описание для раздела или пакета, модуля, класса, метода, функции и т.п.', verbose_name='Описание'),
        ),
        migrations.AlterField(
            model_name='reference',
            name='func_proto',
            field=models.CharField(help_text='Для функций/методов. Описание интерфейса, например: <i>my_func(arg, kwarg=None)</i>', blank=True, max_length=250, null=True, verbose_name='Прототип'),
        ),
        migrations.AlterField(
            model_name='reference',
            name='func_result',
            field=models.CharField(help_text='Для функций/методов. Описание результата, например: <i>int</i>.', blank=True, max_length=250, null=True, verbose_name='Результат'),
        ),
        migrations.AlterField(
            model_name='reference',
            name='parent',
            field=models.ForeignKey(help_text='Укажите родительский раздел. Например, для модуля можно указать раздел справки, в которому он относится; для метода &#8212; класс.', blank=True, to='apps.Reference', verbose_name='Родитель', null=True, related_name='children', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='reference',
            name='type',
            field=models.PositiveIntegerField(help_text='Служит для структурирования информации. Справочные статьи разных типов могут выглядеть по-разному.', choices=[(1, 'Раздел справки'), (2, 'Описание пакета'), (3, 'Описание модуля'), (4, 'Описание функции'), (5, 'Описание класса или типа'), (6, 'Описание метода класса или типа')], default=1, verbose_name='Тип статьи'),
        ),
    ]
