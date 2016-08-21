# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-18 08:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0030_auto_20160711_0915'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReferenceMissing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term', models.CharField(max_length=255, unique=True, verbose_name='Термин')),
                ('synonyms', models.TextField(blank=True, verbose_name='Синонимы')),
                ('hits', models.PositiveIntegerField(default=0, verbose_name='Запросы')),
            ],
            options={
                'verbose_name_plural': 'Промахи справочника',
                'verbose_name': 'Промах справочника',
            },
        ),
        migrations.AlterField(
            model_name='book',
            name='isbn',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='ISBN'),
        ),
        migrations.AlterField(
            model_name='book',
            name='isbn_ebook',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='ISBN эл. книги'),
        ),
        migrations.AlterField(
            model_name='historicalbook',
            name='isbn',
            field=models.CharField(blank=True, db_index=True, max_length=20, null=True, verbose_name='ISBN'),
        ),
        migrations.AlterField(
            model_name='historicalbook',
            name='isbn_ebook',
            field=models.CharField(blank=True, db_index=True, max_length=20, null=True, verbose_name='ISBN эл. книги'),
        ),
    ]