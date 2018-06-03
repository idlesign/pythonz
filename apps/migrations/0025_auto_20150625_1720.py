# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0024_auto_20150621_1206'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vacancy',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('time_created', models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)),
                ('time_published', models.DateTimeField(null=True, editable=False, verbose_name='Дата публикации')),
                ('time_modified', models.DateTimeField(null=True, editable=False, verbose_name='Дата редактирования')),
                ('status', models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')])),
                ('supporters_num', models.PositiveIntegerField(verbose_name='Поддержка', default=0)),
                ('src_alias', models.CharField(verbose_name='Идентификатор источника', choices=[('hh', 'hh.ru')], max_length=20)),
                ('src_id', models.CharField(verbose_name='ID в источнике', max_length=50)),
                ('src_place_name', models.CharField(verbose_name='Название места в источнике', max_length=255)),
                ('src_place_id', models.CharField(db_index=True, verbose_name='ID места в источнике', max_length=20)),
                ('title', models.CharField(verbose_name='Название', max_length=255)),
                ('url_site', models.URLField(verbose_name='Страница сайта')),
                ('url_api', models.URLField(null=True, verbose_name='URL API', blank=True)),
                ('url_logo', models.URLField(null=True, verbose_name='URL логотипа', blank=True)),
                ('employer_name', models.CharField(verbose_name='Работодатель', max_length=255)),
                ('salary_from', models.PositiveIntegerField(null=True, verbose_name='Заработная плата', blank=True)),
                ('salary_till', models.PositiveIntegerField(null=True, verbose_name='З/п до', blank=True)),
                ('salary_currency', models.CharField(null=True, verbose_name='Валюта', blank=True, max_length=255)),
            ],
            options={
                'verbose_name_plural': 'Работа',
                'verbose_name': 'Вакансия',
            },
        ),
        migrations.AlterField(
            model_name='article',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='book',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='community',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='discussion',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='event',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='historicalarticle',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='historicalbook',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='historicalcommunity',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='historicaldiscussion',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='historicalevent',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='historicalplace',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='historicalreference',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='historicalvideo',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='place',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='reference',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='user',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='version',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AlterField(
            model_name='video',
            name='status',
            field=models.PositiveIntegerField(verbose_name='Статус', default=1, choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален'), (4, 'В архиве')]),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='last_editor',
            field=models.ForeignKey(null=True, verbose_name='Редактор', blank=True, to=settings.AUTH_USER_MODEL, related_name='vacancy_editors', on_delete=models.CASCADE, help_text='Пользователь, последним отредактировавший объект.'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='place',
            field=models.ForeignKey(null=True, verbose_name='Место', blank=True, to='apps.Place', related_name='vacancies', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='vacancy',
            unique_together=set([('src_alias', 'src_id')]),
        ),
    ]
