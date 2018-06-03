# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.utils.timezone
import etc.models
import apps.generics.models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(verbose_name='last login', default=django.utils.timezone.now)),
                ('is_superuser', models.BooleanField(verbose_name='superuser status', default=False, help_text='Designates that this user has all permissions without explicitly assigning them.')),
                ('username', models.CharField(max_length=30, verbose_name='username', validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username.', 'invalid')], help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True)),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(max_length=75, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(verbose_name='staff status', default=False, help_text='Designates whether the user can log into this admin site.')),
                ('is_active', models.BooleanField(verbose_name='active', default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')),
                ('date_joined', models.DateTimeField(verbose_name='date joined', default=django.utils.timezone.now)),
                ('time_created', models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)),
                ('time_published', models.DateTimeField(verbose_name='Дата публикации', null=True, editable=False)),
                ('time_modified', models.DateTimeField(verbose_name='Дата редактирования', null=True, editable=False)),
                ('status', models.PositiveIntegerField(verbose_name='Статус', choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')], default=1)),
                ('supporters_num', models.PositiveIntegerField(verbose_name='Количество поддержавших', default=0)),
                ('digest_enabled', models.BooleanField(verbose_name='Получать дайджест', default=True, db_index=True, help_text='Включает/отключает еженедельную рассылку с подборкой новых материалов сайта.')),
                ('comments_enabled', models.BooleanField(verbose_name='Разрешить комментарии', default=False, help_text='Включает/отключает систему комментирования Disqus на страницах ваших публикаций.')),
                ('disqus_shortname', models.CharField(max_length=100, verbose_name='Идентификатор Disqus', help_text='Короткое имя (shortname), под которым вы зарегистрировали форум на Disqus.', null=True, blank=True)),
                ('disqus_category_id', models.CharField(max_length=30, verbose_name='Идентификатор категории Disqus', help_text='Если ваш форум на Disqus использует категории, можете указать нужный номер здесь. Это не обязательно.', null=True, blank=True)),
                ('groups', models.ManyToManyField(help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', blank=True, verbose_name='groups', to='auth.Group', related_name='user_set', related_query_name='user')),
            ],
            options={
                'verbose_name': 'Персона',
                'verbose_name_plural': 'Люди',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(verbose_name='Текст')),
                ('text_src', models.TextField(verbose_name='Исходный текст')),
                ('title', models.CharField(max_length=255, verbose_name='Название', unique=True)),
                ('description', models.TextField(verbose_name='Описание', help_text='Пара-тройка предложений, описывающих, о чём пойдёт речь в статье.')),
                ('cover', models.ImageField(max_length=255, verbose_name='Обложка', upload_to=apps.generics.models.get_upload_to, null=True, blank=True)),
                ('year', models.CharField(max_length=10, verbose_name='Год', null=True, blank=True)),
                ('time_created', models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)),
                ('time_published', models.DateTimeField(verbose_name='Дата публикации', null=True, editable=False)),
                ('time_modified', models.DateTimeField(verbose_name='Дата редактирования', null=True, editable=False)),
                ('status', models.PositiveIntegerField(verbose_name='Статус', choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')], default=1)),
                ('supporters_num', models.PositiveIntegerField(verbose_name='Количество поддержавших', default=0)),
                ('linked', models.ManyToManyField(verbose_name='Связанные объекты', to='apps.Article', related_name='linked_rel_+', help_text='Выберите объекты, имеющие отношение к данному.', blank=True)),
                ('submitter', models.ForeignKey(verbose_name='Добавил', to=settings.AUTH_USER_MODEL, related_name='article_submitters', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Статья',
                'verbose_name_plural': 'Статьи',
            },
            bases=(etc.models.InheritedModel, models.Model),
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author', models.CharField(max_length=255, verbose_name='Автор', help_text='Предпочтительно имя и фамилия. Можно указать несколько, разделяя запятыми.<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].')),
                ('translator', models.CharField(max_length=255, verbose_name='Перевод', help_text='Укажите переводчиков, если материал переведён на русский с другого языка. Если переводчик неизвестен, можно указать главного редактора.<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].', null=True, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='Название', unique=True)),
                ('description', models.TextField(verbose_name='Описание', help_text='Аннотация к книге, или другое краткое описание. Без обозначения личного отношения.')),
                ('cover', models.ImageField(max_length=255, verbose_name='Обложка', upload_to=apps.generics.models.get_upload_to, null=True, blank=True)),
                ('year', models.CharField(max_length=10, verbose_name='Год', null=True, blank=True)),
                ('time_created', models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)),
                ('time_published', models.DateTimeField(verbose_name='Дата публикации', null=True, editable=False)),
                ('time_modified', models.DateTimeField(verbose_name='Дата редактирования', null=True, editable=False)),
                ('status', models.PositiveIntegerField(verbose_name='Статус', choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')], default=1)),
                ('supporters_num', models.PositiveIntegerField(verbose_name='Количество поддержавших', default=0)),
                ('isbn', models.CharField(max_length=20, verbose_name='Код ISBN', unique=True, null=True, blank=True)),
                ('isbn_ebook', models.CharField(max_length=20, verbose_name='Код ISBN эл. книги', unique=True, null=True, blank=True)),
                ('linked', models.ManyToManyField(verbose_name='Связанные объекты', to='apps.Book', related_name='linked_rel_+', help_text='Выберите объекты, имеющие отношение к данному.', blank=True)),
                ('submitter', models.ForeignKey(verbose_name='Добавил', to=settings.AUTH_USER_MODEL, related_name='book_submitters', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Книга',
                'verbose_name_plural': 'Книги',
            },
            bases=(etc.models.InheritedModel, models.Model),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(verbose_name='Текст')),
                ('text_src', models.TextField(verbose_name='Исходный текст')),
                ('title', models.CharField(max_length=255, verbose_name='Название', unique=True)),
                ('description', models.TextField(verbose_name='Описание')),
                ('cover', models.ImageField(max_length=255, verbose_name='Обложка', upload_to=apps.generics.models.get_upload_to, null=True, blank=True)),
                ('year', models.CharField(max_length=10, verbose_name='Год', null=True, blank=True)),
                ('time_created', models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)),
                ('time_published', models.DateTimeField(verbose_name='Дата публикации', null=True, editable=False)),
                ('time_modified', models.DateTimeField(verbose_name='Дата редактирования', null=True, editable=False)),
                ('status', models.PositiveIntegerField(verbose_name='Статус', choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')], default=1)),
                ('supporters_num', models.PositiveIntegerField(verbose_name='Количество поддержавших', default=0)),
                ('type', models.PositiveIntegerField(verbose_name='Тип', choices=[(1, 'Встреча'), (3, 'Лекция'), (2, 'Конференция')], default=1)),
            ],
            options={
                'verbose_name': 'Событие',
                'verbose_name_plural': 'События',
            },
            bases=(etc.models.InheritedModel, models.Model),
        ),
        migrations.CreateModel(
            name='EventDetails',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_start', models.DateTimeField(verbose_name='Начало', null=True)),
                ('time_finish', models.DateTimeField(verbose_name='Завершение', null=True)),
            ],
            options={
                'verbose_name': 'Деталь события',
                'verbose_name_plural': 'Детали событий',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Opinion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(verbose_name='Текст')),
                ('text_src', models.TextField(verbose_name='Исходный текст')),
                ('time_created', models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)),
                ('time_published', models.DateTimeField(verbose_name='Дата публикации', null=True, editable=False)),
                ('time_modified', models.DateTimeField(verbose_name='Дата редактирования', null=True, editable=False)),
                ('status', models.PositiveIntegerField(verbose_name='Статус', choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')], default=1)),
                ('supporters_num', models.PositiveIntegerField(verbose_name='Количество поддержавших', default=0)),
                ('object_id', models.PositiveIntegerField(verbose_name='ID объекта', db_index=True)),
                ('content_type', models.ForeignKey(verbose_name='Тип содержимого', to='contenttypes.ContentType', related_name='opinion_opinions', on_delete=models.CASCADE)),
                ('submitter', models.ForeignKey(verbose_name='Автор', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Мнение',
                'verbose_name_plural': 'Мнения',
            },
            bases=(etc.models.InheritedModel, models.Model),
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_created', models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)),
                ('time_published', models.DateTimeField(verbose_name='Дата публикации', null=True, editable=False)),
                ('time_modified', models.DateTimeField(verbose_name='Дата редактирования', null=True, editable=False)),
                ('status', models.PositiveIntegerField(verbose_name='Статус', choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')], default=1)),
                ('supporters_num', models.PositiveIntegerField(verbose_name='Количество поддержавших', default=0)),
                ('user_title', models.CharField(max_length=255, verbose_name='Название')),
                ('geo_title', models.TextField(verbose_name='Полное название', null=True, blank=True)),
                ('geo_bounds', models.CharField(max_length=255, verbose_name='Пределы', null=True, blank=True)),
                ('geo_pos', models.CharField(max_length=255, verbose_name='Координаты', null=True, blank=True)),
                ('geo_type', models.CharField(max_length=25, choices=[('country', 'Страна'), ('locality', 'Местность'), ('house', 'Здание')], db_index=True, blank=True, verbose_name='Тип', null=True)),
            ],
            options={
                'verbose_name': 'Место',
                'verbose_name_plural': 'Места',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author', models.CharField(max_length=255, verbose_name='Автор', help_text='Предпочтительно имя и фамилия. Можно указать несколько, разделяя запятыми.<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].')),
                ('translator', models.CharField(max_length=255, verbose_name='Перевод', help_text='Укажите переводчиков, если материал переведён на русский с другого языка. Если переводчик неизвестен, можно указать главного редактора.<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].', null=True, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='Название', unique=True)),
                ('description', models.TextField(verbose_name='Описание', help_text='Краткое описание того, о чём это видео. Без обозначения личного отношения.')),
                ('cover', models.ImageField(max_length=255, verbose_name='Обложка', upload_to=apps.generics.models.get_upload_to, null=True, blank=True)),
                ('year', models.CharField(max_length=10, verbose_name='Год', null=True, blank=True)),
                ('time_created', models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)),
                ('time_published', models.DateTimeField(verbose_name='Дата публикации', null=True, editable=False)),
                ('time_modified', models.DateTimeField(verbose_name='Дата редактирования', null=True, editable=False)),
                ('status', models.PositiveIntegerField(verbose_name='Статус', choices=[(1, 'Черновик'), (2, 'Опубликован'), (3, 'Удален')], default=1)),
                ('supporters_num', models.PositiveIntegerField(verbose_name='Количество поддержавших', default=0)),
                ('code', models.TextField(verbose_name='Код')),
                ('url', models.URLField(verbose_name='URL')),
                ('linked', models.ManyToManyField(verbose_name='Связанные объекты', to='apps.Video', related_name='linked_rel_+', help_text='Выберите объекты, имеющие отношение к данному.', blank=True)),
                ('submitter', models.ForeignKey(verbose_name='Добавил', to=settings.AUTH_USER_MODEL, related_name='video_submitters', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Видео',
                'verbose_name_plural': 'Видео',
            },
            bases=(etc.models.InheritedModel, models.Model),
        ),
        migrations.AlterUniqueTogether(
            name='opinion',
            unique_together=set([('content_type', 'object_id', 'submitter')]),
        ),
        migrations.AddField(
            model_name='eventdetails',
            name='place',
            field=models.ForeignKey(verbose_name='Место', to='apps.Place', related_name='events', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='details',
            field=models.ManyToManyField(verbose_name='Место и время', to='apps.EventDetails', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='linked',
            field=models.ManyToManyField(verbose_name='Связанные объекты', to='apps.Event', related_name='linked_rel_+', help_text='Выберите объекты, имеющие отношение к данному.', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='submitter',
            field=models.ForeignKey(verbose_name='Добавил', to=settings.AUTH_USER_MODEL, related_name='event_submitters', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='place',
            field=models.ForeignKey(help_text='Место вашего пребывания (страна, город, село), чтобы pythonz мог фильтровать интересную вам информацию.', blank=True, verbose_name='Место', to='apps.Place', related_name='users', on_delete=models.CASCADE, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(help_text='Specific permissions for this user.', blank=True, verbose_name='user permissions', to='auth.Permission', related_name='user_set', related_query_name='user'),
            preserve_default=True,
        ),
    ]
