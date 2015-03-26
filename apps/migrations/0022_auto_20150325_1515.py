# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0021_partnerlink'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='location',
            field=models.PositiveIntegerField(choices=[(1, 'На этом сайте'), (2, 'На другом сайте')], help_text='Статью можно написать прямо на этом сайте, либо сформировать статью-ссылку на внешний ресурс.', default=1, verbose_name='Расположение статьи'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='published_by_author',
            field=models.BooleanField(default=True, verbose_name='Я являюсь автором данной статьи'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='source',
            field=models.PositiveIntegerField(choices=[(1, 'Написана на этом сайте'), (2, 'Соскоблена с другого сайта'), (3, 'Взята из RSS')], help_text='Указывает на механизм, при помощи которого статья появилась на сайте.', default=1, verbose_name='Тип источника'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='url',
            field=models.URLField(null=True, help_text='Внешний URL, по которому расположена статья, которой выжелаете поделиться.', blank=False, unique=True, verbose_name='URL статьи'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalarticle',
            name='location',
            field=models.PositiveIntegerField(choices=[(1, 'На этом сайте'), (2, 'На другом сайте')], help_text='Статью можно написать прямо на этом сайте, либо сформировать статью-ссылку на внешний ресурс.', default=1, verbose_name='Расположение статьи'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalarticle',
            name='published_by_author',
            field=models.BooleanField(default=True, verbose_name='Я являюсь автором данной статьи'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalarticle',
            name='source',
            field=models.PositiveIntegerField(choices=[(1, 'Написана на этом сайте'), (2, 'Соскоблена с другого сайта'), (3, 'Взята из RSS')], help_text='Указывает на механизм, при помощи которого статья появилась на сайте.', default=1, verbose_name='Тип источника'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalarticle',
            name='url',
            field=models.URLField(db_index=True, help_text='Внешний URL, по которому расположена статья, которой выжелаете поделиться.', null=True, blank=False, verbose_name='URL статьи'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='community',
            name='description',
            field=models.TextField(help_text=('Сжатая предварительная информация о сообществе (например, направление деятельности). <strong>Без обозначения личного отношения. Личное отношение можно выразить во Мнениях.</strong>',), verbose_name='Описание'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partnerlink',
            name='partner_alias',
            field=models.CharField(db_index=True, verbose_name='Идентфикатор класса партнёра', max_length=50),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reference',
            name='title',
            field=models.CharField(unique=True, help_text=('Здесь следует указать название раздела справки или пакета, модуля, класса, метода, функции и т.п.',), verbose_name='Название', max_length=255),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='version',
            name='text_src',
            field=models.TextField(help_text=('Обзорное, более полное описание нововведений и изменений, произошедших в версии. <strong>Без обозначения личного отношения. Личное отношение можно выразить во Мнениях.</strong>',), verbose_name='Исходный текст'),
            preserve_default=True,
        ),
    ]
