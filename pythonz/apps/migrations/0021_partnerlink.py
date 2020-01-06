# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('apps', '0020_historicalarticle_historicalbook_historicalcommunity_historicaldiscussion_historicalevent_historical'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartnerLink',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField(db_index=True, verbose_name='ID объекта')),
                ('partner_alias', models.CharField(max_length=50, db_index=True, choices=[('booksru', 'books.ru')], verbose_name='Идентфикатор класса партнёра')),
                ('url', models.URLField(help_text='Ссылка на партнёрскую страницу без указания партнёрских данных (идентификатора).', verbose_name='Базовая ссылка')),
                ('description', models.CharField(max_length=255, null=True, blank=True, verbose_name='Описание')),
                ('content_type', models.ForeignKey(related_name='partnerlink_partner_links', on_delete=models.CASCADE, to='contenttypes.ContentType', verbose_name='Тип содержимого')),
            ],
            options={
                'verbose_name_plural': 'Партнёрские ссылки',
                'verbose_name': 'Партнёрская ссылка',
            },
            bases=(models.Model,),
        ),
    ]
