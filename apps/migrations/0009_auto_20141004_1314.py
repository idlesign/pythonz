# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0008_community'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='last_editor',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='article_editors', on_delete=models.CASCADE, verbose_name='Редактор', help_text='Пользователь, последним отредактировавший объект.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='last_editor',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='book_editors', on_delete=models.CASCADE, verbose_name='Редактор', help_text='Пользователь, последним отредактировавший объект.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='community',
            name='last_editor',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='community_editors', on_delete=models.CASCADE, verbose_name='Редактор', help_text='Пользователь, последним отредактировавший объект.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='last_editor',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='event_editors', on_delete=models.CASCADE, verbose_name='Редактор', help_text='Пользователь, последним отредактировавший объект.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='opinion',
            name='last_editor',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='opinion_editors', on_delete=models.CASCADE, verbose_name='Редактор', help_text='Пользователь, последним отредактировавший объект.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='place',
            name='last_editor',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='place_editors', on_delete=models.CASCADE, verbose_name='Редактор', help_text='Пользователь, последним отредактировавший объект.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='last_editor',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='user_editors', on_delete=models.CASCADE, verbose_name='Редактор', help_text='Пользователь, последним отредактировавший объект.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='video',
            name='last_editor',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='video_editors', on_delete=models.CASCADE, verbose_name='Редактор', help_text='Пользователь, последним отредактировавший объект.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='community',
            name='contacts',
            field=models.CharField(max_length=255, verbose_name='Контактные лица', help_text='Контактные лица через запятую, представляющие сообщество, координаторы, основатели.<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].'),
        ),
        migrations.AlterField(
            model_name='community',
            name='description',
            field=models.TextField(verbose_name='Описание', help_text='Сжатая предварительная информация о сообществе, например, направление деятельности.'),
        ),
    ]
