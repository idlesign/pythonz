# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import etc.models
import apps.generics.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0017_auto_20141025_1001'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reference',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Текст')),
                ('text_src', models.TextField(help_text='Подробное описание. Здесь же следует располагать примеры кода.', verbose_name='Исходный текст')),
                ('title', models.CharField(help_text='Здесь следует указать название раздела справки или пакета, модуля, класса, метода, функции и т.п.', verbose_name='Название', max_length=255, unique=True)),
                ('description', models.TextField(help_text='Краткое описание для раздела или пакета, модуля, класса, функции и т.п.', verbose_name='Описание')),
                ('cover', models.ImageField(null=True, blank=True, max_length=255, upload_to=apps.generics.models.get_upload_to, verbose_name='Обложка')),
                ('year', models.CharField(null=True, blank=True, max_length=10, verbose_name='Год')),
                ('time_created', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('time_published', models.DateTimeField(null=True, editable=False, verbose_name='Дата публикации')),
                ('time_modified', models.DateTimeField(null=True, editable=False, verbose_name='Дата редактирования')),
                ('status', models.PositiveIntegerField(choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')], default=1, verbose_name='Статус')),
                ('supporters_num', models.PositiveIntegerField(default=0, verbose_name='Поддержка')),
                ('type', models.PositiveIntegerField(help_text='Служит для структурирования информации. Справочные статьи разных типов могут выглядеть по-разному.', default=1, choices=[(1, 'Раздел справки'), (2, 'Описание пакета'), (3, 'Описание модуля'), (4, 'Описание функции'), (5, 'Описание класса/типа'), (6, 'Описание метода класса/типа')], verbose_name='Тип статьи')),
                ('func_proto', models.CharField(null=True, blank=True, max_length=250, help_text='Для функций/методов. Описание интерфейса: my_func(arg, kwarg=None)', verbose_name='Прототип')),
                ('func_params', models.TextField(null=True, blank=True, help_text='Для функций/методов. Описание параметров функции.', verbose_name='Параметры')),
                ('func_result', models.CharField(null=True, blank=True, max_length=250, help_text='Для функций/методов. Описание результата.', verbose_name='Результат')),
                ('last_editor', models.ForeignKey(blank=True, verbose_name='Редактор', null=True, help_text='Пользователь, последним отредактировавший объект.', to=settings.AUTH_USER_MODEL, related_name='reference_editors', on_delete=models.CASCADE)),
                ('linked', models.ManyToManyField(to='apps.Reference', blank=True, help_text='Выберите объекты, имеющие отношение к данному.', related_name='linked_rel_+', verbose_name='Связанные объекты')),
                ('parent', models.ForeignKey(blank=True, verbose_name='Родитель', null=True, help_text='Укажите родительский раздел. Например, для модуля можно указать раздел справки, в которому он относится; для метода &#8212; класс.', to='apps.Reference', related_name='reference_parents', on_delete=models.CASCADE)),
                ('submitter', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='Добавил', related_name='reference_submitters', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Статьи справочника',
                'verbose_name': 'Статья справочника',
            },
            bases=(etc.models.InheritedModel, models.Model),
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Текст')),
                ('text_src', models.TextField(help_text='Обзорное, более полное описание нововведений и изменений, произошедших в версии. <strong>Без обозначения личного отношения. Личное отношение можно выразить во Мнениях.</strong>', verbose_name='Исходный текст')),
                ('title', models.CharField(verbose_name='Название', max_length=255, unique=True)),
                ('description', models.TextField(help_text='Краткое описание основных изменений в версии.', verbose_name='Описание')),
                ('cover', models.ImageField(null=True, blank=True, max_length=255, upload_to=apps.generics.models.get_upload_to, verbose_name='Обложка')),
                ('year', models.CharField(null=True, blank=True, max_length=10, verbose_name='Год')),
                ('time_created', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('time_published', models.DateTimeField(null=True, editable=False, verbose_name='Дата публикации')),
                ('time_modified', models.DateTimeField(null=True, editable=False, verbose_name='Дата редактирования')),
                ('status', models.PositiveIntegerField(choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')], default=1, verbose_name='Статус')),
                ('supporters_num', models.PositiveIntegerField(default=0, verbose_name='Поддержка')),
                ('current', models.BooleanField(db_index=True, default=False, verbose_name='Текущая')),
                ('last_editor', models.ForeignKey(blank=True, verbose_name='Редактор', null=True, help_text='Пользователь, последним отредактировавший объект.', to=settings.AUTH_USER_MODEL, related_name='version_editors', on_delete=models.CASCADE)),
                ('linked', models.ManyToManyField(to='apps.Version', blank=True, help_text='Выберите объекты, имеющие отношение к данному.', related_name='linked_rel_+', verbose_name='Связанные объекты')),
                ('submitter', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='Добавил', related_name='version_submitters', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Версии Python',
                'verbose_name': 'Версия Python',
            },
            bases=(etc.models.InheritedModel, models.Model),
        ),
        migrations.AddField(
            model_name='reference',
            name='version_added',
            field=models.ForeignKey(blank=True, verbose_name='Добавлено в', null=True, help_text='Версия Python, для которой впервые стала актульна данная статья<br>(версия, где впервые появился модуль, пакет, класс, функция).', to='apps.Version', related_name='reference_added', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reference',
            name='version_deprecated',
            field=models.ForeignKey(blank=True, verbose_name='Устарело в', null=True, help_text='Версия Python, для которой впервые данная статья перестала быть актуальной<br>(версия, где модуль, пакет, класс, функция были объявлены устаревшими).', to='apps.Version', related_name='reference_deprecated', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
