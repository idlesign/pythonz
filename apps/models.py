from collections import OrderedDict

import requests
from etc.models import InheritedModel
from sitecats.models import ModelWithCategory
from django.db import models, IntegrityError
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

    def get_title(self):
        """Формирует и возвращает заголовок для мнения.

        :return:
        """
        return '%s про «%s»' % (self.submitter.get_display_name(), self.linked_object.title)
    title = property(get_title)

    def save(self, *args, **kwargs):
        self.status = self.STATUS_PUBLISHED  # Авторский материал не нуждается в модерации %)
        super().save(*args, **kwargs)

    @classmethod
    def get_paginator_objects(cls):
        return cls.objects.select_related('submitter').filter(status=cls.STATUS_PUBLISHED).order_by('-time_created').all()

    def __unicode__(self):
        return 'Мнение %s для %s %s' % (self.id, self.content_type, self.object_id)


class ModelWithOpinions(models.Model):
    """Класс-примесь к моделям сущностей, для который разрешено оставление мнений."""

    opinions = generic.GenericRelation(Opinion)

    class Meta:
        abstract = True


class Place(RealmBaseModel, ModelWithOpinions):
    """Географическое место. Для людей, событий и пр."""

    TYPE_COUNTRY = 'country'
    TYPE_LOCALITY = 'locality'
    TYPE_HOUSE = 'house'

    TYPES = (
        (TYPE_COUNTRY, 'Страна'),
        (TYPE_LOCALITY, 'Местность'),
        (TYPE_HOUSE, 'Здание'),
    )

    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True, null=False, default='')
    geo_title = models.TextField('Полное название', null=True, blank=True, unique=True)
    geo_bounds = models.CharField('Пределы', max_length=255, null=True, blank=True)
    geo_pos = models.CharField('Координаты', max_length=255, null=True, blank=True)
    geo_type = models.CharField('Тип', max_length=25, null=True, blank=True, choices=TYPES, db_index=True)

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    @classmethod
    def create_place_from_name(cls, name):
        """Создаёт место по его имени.

        :param name:
        :return:
        """
        from .utils import get_location_data
        loc_data = get_location_data(name)
        if loc_data is None:
            return None

        full_title = loc_data['name']
        place = cls(
            title=loc_data['requested_name'],
            geo_title=full_title,
            geo_bounds=loc_data['bounds'],
            geo_pos=loc_data['pos'],
            geo_type=loc_data['type']
        )
        try:
            place.save()
        except IntegrityError:
            place = cls.objects.get(geo_title=full_title)
        return place

    def __unicode__(self):
        return self.geo_title


class Community(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithOpinions, ModelWithCategory, ModelWithCompiledText):
    """Модель сообществ. Формально объединяет некоторую группу людей."""

    place = models.ForeignKey(Place, verbose_name='Место', related_name='communities', null=True, blank=True,
        help_text='Для географически локализованных сообществ можно указать место (страна, город, село).<br>Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».')
    url = models.URLField('Страница в сети', null=True, blank=True)
    contacts = models.CharField('Контактные лица', help_text='Контактные лица через запятую, представляющие сообщество, координаторы, основатели.%s' % ModelWithAuthorAndTranslator._hint_userlink, null=True, blank=True, max_length=255)

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'

    class Fields:
        title = 'Название сообщества'
        text_src = 'Описание, контактная информация'
        description = {
            'verbose_name': 'Кратко',
            'help_text': 'Сжатая предварительная информация о сообществе, например, направление деятельности.',
        }
        linked = {
            'verbose_name': 'Связанные сообщества',
            'help_text': 'Выберите сообщества, имеющие отношение к данному.',
        }
        year = 'Год образования'


class User(RealmBaseModel, AbstractUser):
    """Наша модель пользователей."""

    place = models.ForeignKey(Place, verbose_name='Место', help_text='Место вашего пребывания (страна, город, село).<br>Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».', related_name='users', null=True, blank=True)
    digest_enabled = models.BooleanField('Получать дайджест', help_text='Включает/отключает еженедельную рассылку с подборкой новых материалов сайта.', default=True, db_index=True)
    comments_enabled = models.BooleanField('Разрешить комментарии', help_text='Включает/отключает систему комментирования Disqus на страницах ваших публикаций.', default=False)
    disqus_shortname = models.CharField('Идентификатор Disqus', help_text='Короткое имя (shortname), под которым вы зарегистрировали форум на Disqus.', max_length=100, null=True, blank=True)
    disqus_category_id = models.CharField('Идентификатор категории Disqus', help_text='Если ваш форум на Disqus использует категории, можете указать нужный номер здесь. Это не обязательно.', max_length=30, null=True, blank=True)
    timezone = models.CharField('Часовой пояс', help_text='Название часового пояса. Например: Asia/Novosibirsk.<br>* Устанавливается автоматически в зависимости от места пребывания (см. выше).', max_length=150, null=True, blank=True)
    url = models.URLField('Страница в сети', null=True, blank=True)
    email_public = models.EmailField('Почта', help_text='Адрес электронной почты для показа посетителям сайта.', null=True, blank=True)

    class Meta:
        verbose_name = 'Персона'
        verbose_name_plural = 'Люди'

    def set_timezone_from_place(self):
        if self.place is None:
            self.timezone = None
            return True
        from .utils import get_timezone_name
        lat, lng = self.place.geo_pos.split(',')
        self.timezone = get_timezone_name(lat, lng)

    def get_bookmarks(self):
        """Возвращает словарь с избранными пользователем эелементами (закладками).
        Словарь индексирован классами моделей различных сущностей, в значениях - списки с самими сущностями.

        :return:
        """
        from siteflags.utils import get_flag_model
        from .realms import get_realms

        FLAG_MODEL = get_flag_model()
        realm_models = [r.model for r in get_realms()]
        bookmarks = FLAG_MODEL.get_flags_for_types(realm_models, user=self, status=RealmBaseModel.FLAG_STATUS_BOOKMARK)
        for realm_model, flags in bookmarks.items():
            ids = [flag.object_id for flag in flags]
            items = realm_model.objects.filter(id__in=ids)
            bookmarks[realm_model] = items
        return bookmarks

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
    title = property(get_display_name)

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

    url = models.URLField('Страница в сети', null=True, blank=True)
    contacts = models.CharField('Контактные лица', help_text='Контактные лица через запятую, координирующие/устраивающие событие.%s' % ModelWithAuthorAndTranslator._hint_userlink, null=True, blank=True, max_length=255)
    type = models.PositiveIntegerField('Тип', choices=TYPES, default=TYPE_MEETING)
    time_start = models.DateTimeField('Начало', null=True, blank=True)
    time_finish = models.DateTimeField('Завершение', null=True, blank=True)
    place = models.ForeignKey(Place, verbose_name='Место', related_name='events', null=True, blank=True,
          help_text='Укажите место проведения мероприятия.<br><b>Конкретный адрес следует указывать в описании.</b><br>Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».')

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    class Fields:
        text = 'Описание'
        text_src = 'Описание'
        cover = 'Логотип'
