from collections import OrderedDict

import requests
from etc.models import InheritedModel
from sitecats.models import ModelWithCategory
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from .generics.models import CommonEntityModel, ModelWithCompiledText, ModelWithAuthorAndTranslator, RealmBaseModel
from .exceptions import PythonzException


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class Opinion(InheritedModel, RealmBaseModel, ModelWithCompiledText):
    """Модель мнений. Пользователи могут поделится своим менением по попову той или иной сущности на сайте.
    Фактически - комментарии.
    """

    submitter = models.ForeignKey(USER_MODEL, verbose_name='Автор')

    object_id = models.PositiveIntegerField(verbose_name='ID объекта', db_index=True)
    content_type = models.ForeignKey(ContentType, verbose_name='Тип содержимого', related_name='%(class)s_opinions')

    linked_object = generic.GenericForeignKey()

    class Meta:
        verbose_name = 'Мнение'
        verbose_name_plural = 'Мнения'
        unique_together = ('content_type', 'object_id', 'submitter')

    class Fields:
        text = 'Мнение'

    txt_promo = 'Мнения отражают картину мира людей. Делитесь своим, уважайте чужое. Добро пожаловать в картинную галерею.'
    txt_form_add = 'Добавить мнение'
    txt_form_edit = 'Изменить мнение'

    @classmethod
    def get_paginator_objects(cls):
        return cls.objects.select_related('submitter').order_by('-id').all()

    def __unicode__(self):
        return 'Мнение %s для %s %s' % (self.id, self.content_type, self.object_id)


class ModelWithOpinions(models.Model):
    """Класс-примесь к моделям сущностей, для который разрешено оставление мнений."""

    opinions = generic.GenericRelation(Opinion)

    class Meta:
        abstract = True


class Place(RealmBaseModel):
    """Географическое место. Для людей, событий и пр."""

    TYPE_COUNTRY = 'country'
    TYPE_LOCALITY = 'locality'
    TYPE_HOUSE = 'house'

    TYPES = (
        (TYPE_COUNTRY, 'Страна'),
        (TYPE_LOCALITY, 'Местность'),
        (TYPE_HOUSE, 'Здание'),
    )

    user_title = models.CharField('Название', max_length=255)
    geo_title = models.TextField('Полное название', null=True, blank=True)
    geo_bounds = models.CharField('Пределы', max_length=255, null=True, blank=True)
    geo_pos = models.CharField('Координаты', max_length=255, null=True, blank=True)
    geo_type = models.CharField('Тип', max_length=25, null=True, blank=True, choices=TYPES, db_index=True)

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    txt_promo = 'В какую точку земного шара ни ткни, почти наверняка там найдутся интересные люди. Отправлятесь искать клад.'


class User(RealmBaseModel, AbstractUser):
    """Наша модель пользователей."""

    place = models.ForeignKey(Place, verbose_name='Место', help_text='Место вашего пребывания (страна, город, село), чтобы pythonz мог фильтровать интересную вам информацию.', related_name='users', null=True, blank=True)
    digest_enabled = models.BooleanField('Получать дайджест', help_text='Включает/отключает еженедельную рассылку с подборкой новых материалов сайта.', default=True, db_index=True)
    comments_enabled = models.BooleanField('Разрешить комментарии', help_text='Включает/отключает систему комментирования Disqus на страницах ваших публикаций.', default=False)
    disqus_shortname = models.CharField('Идентификатор Disqus', help_text='Короткое имя (shortname), под которым вы зарегистрировали форум на Disqus.', max_length=100, null=True, blank=True)
    disqus_category_id = models.CharField('Идентификтаор категории Disqus', help_text='Если ваш форум на Disqus использует категории, можете указать нужный номер здесь. Это не обязательно.', max_length=30, null=True, blank=True)

    class Meta:
        verbose_name = 'Персона'
        verbose_name_plural = 'Люди'

    txt_promo = 'Вокруг люди &#8211; это они пишут статьи и книги, организовывают встречи и делятся мнениями, это они могут помочь, подсказать, научить. Здесь упомянуты некоторые.'
    txt_form_edit = 'Изменить настройки'

    @classmethod
    def get_digest_subsribers(cls):
        """Возвращает выборку пользователей, подписанных на еженедельный дайджест.

        :return:
        """
        return cls.objects.filter(is_active=True, digest_enabled=True).all()

    @classmethod
    def get_actual(cls):
        return cls.objects.filter(is_active=True).order_by('-date_joined').all()

    @classmethod
    def get_paginator_objects(cls):
        return cls.objects.order_by('-supporters_num', '-date_joined').all()

    def get_display_name(self):
        return self.get_full_name() or self.get_username_partial()

    def get_username_partial(self):
        return self.username.split('@')[0]


class Book(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithOpinions, ModelWithCategory, ModelWithAuthorAndTranslator):
    """Модель сущности `Книга`."""

    COVER_UPLOAD_TO = 'books'

    isbn = models.CharField('Код ISBN', max_length=20, unique=True, null=True, blank=True)
    isbn_ebook = models.CharField('Код ISBN эл. книги', max_length=20, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'

    class Fields:
        title = 'Название книги'
        description = {
            'verbose_name': 'Аннотация',
            'help_text': 'Аннотация к книге, или другое краткое описание. Без обозначения личного отношения.',
        }
        linked = {
            'verbose_name': 'Связанные книги',
            'help_text': 'Выберите книги, которые имеют отношение к данной. Например, для книги-перевода можно указать оригинал.',
        }
        year = 'Год издания'

    txt_promo = 'Времена и люди сменяют друг друга, а книги остаются. Взгляните на них &#8211; фолианты, книжицы и книжонки. Ходят слухи, что здесь можно отыскать даже гримуары.'
    txt_form_add = 'Добавить книгу'
    txt_form_edit = 'Изменить данные книги'


class Article(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithOpinions, ModelWithCategory, ModelWithCompiledText):
    """Модель сущности `Статья`."""

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

    class Fields:
        description = {
            'verbose_name': 'Введение',
            'help_text': 'Пара-тройка предложений, описывающих, о чём пойдёт речь в статье.',
        }
        linked = {
            'verbose_name': 'Связанные статьи',
            'help_text': 'Выберите статьи, которые имеют отношение к данной. Так, например, можно объединить статьи цикла.',
        }

    txt_promo = 'Статьи похожи на рассказы. Хорошие статьи, как и хорошие рассказы, хочется читать часто, много и даже с наслаждением.'
    txt_form_add = 'Написать статью'
    txt_form_edit = 'Редактировать статью'


class Video(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithOpinions, ModelWithCategory, ModelWithAuthorAndTranslator):
    """Модель сущности `Видео`."""

    EMBED_WIDTH = 560
    EMBED_HEIGHT = 315
    COVER_UPLOAD_TO = 'videos'

    code = models.TextField('Код')
    url = models.URLField('URL')

    class Meta:
        verbose_name = 'Видео'
        verbose_name_plural = 'Видео'

    class Fields:
        title = 'Название видео'
        description = {
            'help_text': 'Краткое описание того, о чём это видео. Без обозначения личного отношения.',
        }
        linked = {
            'verbose_name': 'Связанные видео',
            'help_text': 'Выберите видео, которые имеют отношение к данному. Например, можно связать несколько эпизодов видео.',
        }
        year = 'Год съёмок'

    txt_promo = 'Видео уникально в плане возможностей по усвоению материала: оно заставляет смотреть, слушать, и даже читать. Попробуйте, вам должно понравится.'
    txt_form_add = 'Добавить видео'
    txt_form_edit = 'Изменить данные видео'

    _supported_hostings = OrderedDict(sorted({
        'Vimeo': ('vimeo.com', 'vimeo'),
        'YouTube': ('youtu', 'youtube'),
    }.items(), key=lambda k: k[0]))

    @classmethod
    def get_supported_hostings(cls):
        return cls._supported_hostings.keys()

    @classmethod
    def get_data_from_vimeo(cls, url):
        if 'vimeo.com' in url:  # http://vimeo.com/{id}
            video_id = url.rsplit('/', 1)[-1]
        else:
            raise PythonzException('Unable to get parse video ID from `%s`' % url)

        embed_code = '<iframe src="//player.vimeo.com/video/%s?byline=0&amp;portrait=0&amp;color=ffffff" width="%s" height="%s" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>' % (video_id, cls.EMBED_WIDTH, cls.EMBED_HEIGHT)

        response = requests.get('http://vimeo.com/api/v2/video/%s.json' % video_id)
        cover_url = response.json()[0]['thumbnail_small']

        return embed_code, cover_url

    @classmethod
    def get_data_from_youtube(cls, url):
        if 'youtu.be' in url:  # http://youtu.be/{id}
            video_id = url.rsplit('/', 1)[-1]
        elif 'watch?v=' in url:  # http://www.youtube.com/watch?v={id}
            video_id = url.rsplit('v=', 1)[-1]
        else:
            raise PythonzException('Unable to get parse video ID from `%s`' % url)

        embed_code = '<iframe src="//www.youtube.com/embed/%s?rel=0" width="%s" height="%s" frameborder="0" allowfullscreen></iframe>' % (video_id, cls.EMBED_WIDTH, cls.EMBED_HEIGHT)
        cover_url = 'http://img.youtube.com/vi/%s/default.jpg' % video_id
        return embed_code, cover_url

    @classmethod
    def get_hosting_for_url(cls, url):
        hosting = None
        for title, data in cls._supported_hostings.items():
            search_str, hid = data
            if search_str in url:
                hosting = hid
                break
        return hosting

    def update_code_and_cover(self, url):
        url = url.rstrip('/')
        hid = self.get_hosting_for_url(url)
        if hid is None:
            raise PythonzException('Unable to get hosting for URL `%s`' % url)

        method_name = 'get_data_from_%s' % hid
        method = getattr(self, method_name, None)
        if method is None:
            raise PythonzException('Unable to locate `%s` method' % method_name)

        embed_code, cover_url = method(url)

        self.code = embed_code
        self.update_cover_from_url(cover_url)


class EventDetails(models.Model):
    """Модель детальной информации для сущности `Событие`."""

    place = models.ForeignKey(Place, verbose_name='Место', related_name='events')
    time_start = models.DateTimeField('Начало', null=True)
    time_finish = models.DateTimeField('Завершение', null=True)

    class Meta:
        verbose_name = 'Деталь события'
        verbose_name_plural = 'Детали событий'


class Event(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithOpinions, ModelWithCompiledText):
    """Модель сущности `Событие`."""

    TYPE_MEETING = 1
    TYPE_CONFERENCE = 2
    TYPE_LECTURE = 3

    TYPES = (
        (TYPE_MEETING, 'Встреча'),
        (TYPE_LECTURE, 'Лекция'),
        (TYPE_CONFERENCE, 'Конференция'),
    )

    type = models.PositiveIntegerField('Тип', choices=TYPES, default=TYPE_MEETING)
    details = models.ManyToManyField(EventDetails, verbose_name='Место и время', null=True, blank=True)

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    class Fields:
        text = 'Описание'
        text_src = 'Описание'

    txt_promo = 'События разнообразят жизнь: встречи, лекции, беседы, обмен опытом позволяют расширить кругозор, установить связи, приятно провести время. Приобщайтесь.'
    txt_form_add = 'Добавить событие'
    txt_form_edit = 'Изменить событие'
