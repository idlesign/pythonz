# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0022_auto_20150325_1515'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='slug',
            field=models.CharField(max_length=200, verbose_name='Краткое имя для URL', null=True, blank=True, unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='slug',
            field=models.CharField(max_length=200, verbose_name='Краткое имя для URL', null=True, blank=True, unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='community',
            name='slug',
            field=models.CharField(max_length=200, verbose_name='Краткое имя для URL', null=True, blank=True, unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='discussion',
            name='slug',
            field=models.CharField(max_length=200, verbose_name='Краткое имя для URL', null=True, blank=True, unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='slug',
            field=models.CharField(max_length=200, verbose_name='Краткое имя для URL', null=True, blank=True, unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalarticle',
            name='slug',
            field=models.CharField(blank=True, verbose_name='Краткое имя для URL', null=True, db_index=True, max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalbook',
            name='slug',
            field=models.CharField(blank=True, verbose_name='Краткое имя для URL', null=True, db_index=True, max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalcommunity',
            name='slug',
            field=models.CharField(blank=True, verbose_name='Краткое имя для URL', null=True, db_index=True, max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicaldiscussion',
            name='slug',
            field=models.CharField(blank=True, verbose_name='Краткое имя для URL', null=True, db_index=True, max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalevent',
            name='slug',
            field=models.CharField(blank=True, verbose_name='Краткое имя для URL', null=True, db_index=True, max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalreference',
            name='slug',
            field=models.CharField(blank=True, verbose_name='Краткое имя для URL', null=True, db_index=True, max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historicalvideo',
            name='slug',
            field=models.CharField(blank=True, verbose_name='Краткое имя для URL', null=True, db_index=True, max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reference',
            name='slug',
            field=models.CharField(max_length=200, verbose_name='Краткое имя для URL', null=True, blank=True, unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='version',
            name='slug',
            field=models.CharField(max_length=200, verbose_name='Краткое имя для URL', null=True, blank=True, unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='video',
            name='slug',
            field=models.CharField(max_length=200, verbose_name='Краткое имя для URL', null=True, blank=True, unique=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='article',
            name='url',
            field=models.URLField(verbose_name='URL статьи', null=True, unique=True, help_text='Внешний URL, по которому доступна статья, которой вы желаете поделиться.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='historicalarticle',
            name='url',
            field=models.URLField(verbose_name='URL статьи', null=True, db_index=True, help_text='Внешний URL, по которому доступна статья, которой вы желаете поделиться.'),
            preserve_default=True,
        ),
    ]
