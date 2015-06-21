# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.contrib.auth.models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('apps', '0023_auto_20150331_1711'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalarticle',
            options={'verbose_name': 'historical Статья', 'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id')},
        ),
        migrations.AlterModelOptions(
            name='historicalbook',
            options={'verbose_name': 'historical Книга', 'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id')},
        ),
        migrations.AlterModelOptions(
            name='historicalcommunity',
            options={'verbose_name': 'historical Сообщество', 'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id')},
        ),
        migrations.AlterModelOptions(
            name='historicaldiscussion',
            options={'verbose_name': 'historical Обсуждение', 'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id')},
        ),
        migrations.AlterModelOptions(
            name='historicalevent',
            options={'verbose_name': 'historical Событие', 'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id')},
        ),
        migrations.AlterModelOptions(
            name='historicalplace',
            options={'verbose_name': 'historical Место', 'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id')},
        ),
        migrations.AlterModelOptions(
            name='historicalreference',
            options={'verbose_name': 'historical Статья справочника', 'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id')},
        ),
        migrations.AlterModelOptions(
            name='historicalvideo',
            options={'verbose_name': 'historical Видео', 'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id')},
        ),
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.RemoveField(
            model_name='historicalarticle',
            name='last_editor_id',
        ),
        migrations.RemoveField(
            model_name='historicalarticle',
            name='submitter_id',
        ),
        migrations.RemoveField(
            model_name='historicalbook',
            name='last_editor_id',
        ),
        migrations.RemoveField(
            model_name='historicalbook',
            name='submitter_id',
        ),
        migrations.RemoveField(
            model_name='historicalcommunity',
            name='last_editor_id',
        ),
        migrations.RemoveField(
            model_name='historicalcommunity',
            name='place_id',
        ),
        migrations.RemoveField(
            model_name='historicalcommunity',
            name='submitter_id',
        ),
        migrations.RemoveField(
            model_name='historicaldiscussion',
            name='content_type_id',
        ),
        migrations.RemoveField(
            model_name='historicaldiscussion',
            name='last_editor_id',
        ),
        migrations.RemoveField(
            model_name='historicaldiscussion',
            name='submitter_id',
        ),
        migrations.RemoveField(
            model_name='historicalevent',
            name='last_editor_id',
        ),
        migrations.RemoveField(
            model_name='historicalevent',
            name='place_id',
        ),
        migrations.RemoveField(
            model_name='historicalevent',
            name='submitter_id',
        ),
        migrations.RemoveField(
            model_name='historicalplace',
            name='last_editor_id',
        ),
        migrations.RemoveField(
            model_name='historicalreference',
            name='last_editor_id',
        ),
        migrations.RemoveField(
            model_name='historicalreference',
            name='parent_id',
        ),
        migrations.RemoveField(
            model_name='historicalreference',
            name='submitter_id',
        ),
        migrations.RemoveField(
            model_name='historicalreference',
            name='version_added_id',
        ),
        migrations.RemoveField(
            model_name='historicalreference',
            name='version_deprecated_id',
        ),
        migrations.RemoveField(
            model_name='historicalvideo',
            name='last_editor_id',
        ),
        migrations.RemoveField(
            model_name='historicalvideo',
            name='submitter_id',
        ),
        migrations.AddField(
            model_name='historicalarticle',
            name='last_editor',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalarticle',
            name='submitter',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalbook',
            name='last_editor',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalbook',
            name='submitter',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalcommunity',
            name='last_editor',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalcommunity',
            name='place',
            field=models.ForeignKey(null=True, to='apps.Place', db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalcommunity',
            name='submitter',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicaldiscussion',
            name='content_type',
            field=models.ForeignKey(null=True, to='contenttypes.ContentType', db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicaldiscussion',
            name='last_editor',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicaldiscussion',
            name='submitter',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalevent',
            name='last_editor',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalevent',
            name='place',
            field=models.ForeignKey(null=True, to='apps.Place', db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalevent',
            name='submitter',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalplace',
            name='last_editor',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalreference',
            name='last_editor',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalreference',
            name='parent',
            field=models.ForeignKey(null=True, to='apps.Reference', db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalreference',
            name='submitter',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalreference',
            name='version_added',
            field=models.ForeignKey(null=True, to='apps.Version', db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalreference',
            name='version_deprecated',
            field=models.ForeignKey(null=True, to='apps.Version', db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalvideo',
            name='last_editor',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='historicalvideo',
            name='submitter',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, db_constraint=False, blank=True, related_name='+', on_delete=django.db.models.deletion.DO_NOTHING),
        ),
        migrations.AlterField(
            model_name='community',
            name='description',
            field=models.TextField(verbose_name='Описание', help_text='Сжатая предварительная информация о сообществе (например, направление деятельности). <strong>Без обозначения личного отношения. Личное отношение можно выразить во Мнениях.</strong>'),
        ),
        migrations.AlterField(
            model_name='historicalarticle',
            name='history_user',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='+', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='historicalbook',
            name='history_user',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='+', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='historicalcommunity',
            name='history_user',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='+', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='historicaldiscussion',
            name='history_user',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='+', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='historicalevent',
            name='history_user',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='+', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='historicalplace',
            name='history_user',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='+', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='historicalreference',
            name='history_user',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='+', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='historicalreference',
            name='type',
            field=models.PositiveIntegerField(verbose_name='Тип статьи', choices=[(1, 'Раздел справки'), (2, 'Описание пакета'), (3, 'Описание модуля'), (4, 'Описание функции'), (5, 'Описание класса/типа'), (6, 'Описание метода класса/типа'), (7, 'Описание свойства класса/типа')], default=1, help_text='Служит для структурирования информации. Справочные статьи разных типов могут выглядеть по-разному.'),
        ),
        migrations.AlterField(
            model_name='historicalvideo',
            name='history_user',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='+', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='reference',
            name='type',
            field=models.PositiveIntegerField(verbose_name='Тип статьи', choices=[(1, 'Раздел справки'), (2, 'Описание пакета'), (3, 'Описание модуля'), (4, 'Описание функции'), (5, 'Описание класса/типа'), (6, 'Описание метода класса/типа'), (7, 'Описание свойства класса/типа')], default=1, help_text='Служит для структурирования информации. Справочные статьи разных типов могут выглядеть по-разному.'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(verbose_name='email address', max_length=254, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='email_public',
            field=models.EmailField(verbose_name='Эл. почта', null=True, max_length=254, help_text='Адрес электронной почты для показа посетителям сайта.', blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', blank=True, related_query_name='user', verbose_name='groups', to='auth.Group', related_name='user_set'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_login',
            field=models.DateTimeField(verbose_name='last login', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], error_messages={'unique': 'A user with that username already exists.'}, max_length=30, help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', verbose_name='username', unique=True),
        ),
    ]
