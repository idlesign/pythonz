# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import apps.generics.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0014_auto_20141023_1450'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='discussion',
            options={'verbose_name': 'Обсуждение', 'verbose_name_plural': 'Обсуждения'},
        ),
        migrations.AddField(
            model_name='discussion',
            name='cover',
            field=models.ImageField(verbose_name='Обложка', blank=True, null=True, upload_to=apps.generics.models.get_upload_to, max_length=255),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='discussion',
            name='description',
            field=models.TextField(verbose_name='Описание', default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='discussion',
            name='linked',
            field=models.ManyToManyField(verbose_name='Связанные объекты', blank=True, related_name='linked_rel_+', to='apps.Discussion', help_text='Выберите объекты, имеющие отношение к данному.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='discussion',
            name='title',
            field=models.CharField(verbose_name='Название', default='', max_length=255, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='discussion',
            name='year',
            field=models.CharField(verbose_name='Год', blank=True, null=True, max_length=10),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='discussion',
            name='content_type',
            field=models.ForeignKey(related_name='discussion_opinions', on_delete=models.CASCADE, null=True, verbose_name='Тип содержимого', blank=True, to='contenttypes.ContentType'),
        ),
        migrations.AlterField(
            model_name='discussion',
            name='object_id',
            field=models.PositiveIntegerField(verbose_name='ID объекта', blank=True, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='discussion',
            name='submitter',
            field=models.ForeignKey(related_name='discussion_submitters', on_delete=models.CASCADE, verbose_name='Добавил', to=settings.AUTH_USER_MODEL),
        ),
    ]
