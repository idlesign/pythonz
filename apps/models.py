from collections import OrderedDict

import requests
from etc.models import InheritedModel
from etc.toolbox import choices_list, get_choices
from sitecats.models import ModelWithCategory
from simple_history.models import HistoricalRecords
from django.db import models, IntegrityError
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils import timezone

from .generics.models import CommonEntityModel, ModelWithCompiledText, ModelWithAuthorAndTranslator, RealmBaseModel
from .exceptions import RemoteSourceError
from .utils import scrape_page, HhVacancyManager


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')

HINT_IMPERSONAL_REQUIRED = ('<strong>Без обозначения личного отношения. '
                            'Личное отношение можно выразить во Мнениях.</strong>')


class Discussion(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithCategory, ModelWithCompiledText):
    """Модель обсуждений. Пользователи могут обсудить желаемые темы и привязать обсужедние к сущности на сайте.
    Фактически - форум.
    """

    object_id = models.PositiveIntegerField(verbose_name='ID объекта', db_index=True, null=True, blank=True)
    content_type = models.ForeignKey(
        ContentType, verbose_name='Тип содержимого', related_name='%(class)s_discussions', null=True, blank=True)

    linked_object = generic.GenericForeignKey()

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Обсуждение'
        verbose_name_plural = 'Обсуждения'

    class Fields:
        text = 'Обсуждение'

    def __unicode__(self):
        return 'Обсуждение %s для %s %s' % (self.id, self.content_type, self.object_id)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.status = self.STATUS_PUBLISHED
        super().save(*args, **kwargs)


class ModelWithDiscussions(models.Model):
    """Класс-примесь к моделям сущностей, для который разрешено оставление мнений."""

    discussions = generic.GenericRelation(Discussion)

    class Meta:
        abstract = True


class PartnerLink(models.Model):
    """Модель партнёрских ссылок. Ссылки могут быть привязаны к любым сущностям сайта.
    Логику формирования и отображения ссылок предоставляют классы из модуля partners.

    """

    object_id = models.PositiveIntegerField(verbose_name='ID объекта', db_index=True)
    content_type = models.ForeignKey(
        ContentType, verbose_name='Тип содержимого', related_name='%(class)s_partner_links')

    partner_alias = models.CharField('Идентфикатор класса партнёра', max_length=50, db_index=True)

    url = models.URLField(
        'Базовая ссылка', help_text='Ссылка на партнёрскую страницу без указания партнёрских данных (идентификатора).')

    description = models.CharField('Описание', max_length=255, null=True, blank=True)

    linked_object = generic.GenericForeignKey()

    class Meta:
        verbose_name = 'Партнёрская ссылка'
        verbose_name_plural = 'Партнёрские ссылки'

    def __unicode__(self):
        return 'Партнёрская ссылка %s для %s %s' % (self.id, self.content_type, self.object_id)


class ModelWithPartnerLinks(models.Model):
    """Класс-примесь к моделям сущностей, для который разрешено добавление партнёрских ссылок."""

    partner_links = generic.GenericRelation(PartnerLink)

    class Meta:
        abstract = True


class Place(RealmBaseModel, ModelWithDiscussions):
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

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def get_pos(self):
        """Возвращает координаты объекта в виде кортежа: (широта, долгота).

        :return:
        """
        lat, lng = self.geo_pos.split('|')
        return lat, lng

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


class Vacancy(RealmBaseModel):

    SRC_ALIAS_HH = 'hh'

    SRC_ALIASES = (
        (SRC_ALIAS_HH, 'hh.ru'),
    )

    MANAGERS = OrderedDict([
        (SRC_ALIAS_HH, HhVacancyManager)
    ])

    src_alias = models.CharField('Идентификатор источника', max_length=20, choices=SRC_ALIASES)
    src_id = models.CharField('ID в источнике', max_length=50)
    src_place_name = models.CharField('Название места в источнике', max_length=255)
    src_place_id = models.CharField('ID места в источнике', max_length=20, db_index=True)

    title = models.CharField('Название', max_length=255)
    url_site = models.URLField('Страница сайта')
    url_api = models.URLField('URL API', null=True, blank=True)
    url_logo = models.URLField('URL логотипа', null=True, blank=True)

    employer_name = models.CharField('Работодатель', max_length=255)

    place = models.ForeignKey(Place, verbose_name='Место', related_name='vacancies', null=True, blank=True)
    salary_from = models.PositiveIntegerField('Заработная плата', null=True, blank=True)
    salary_till = models.PositiveIntegerField('З/п до', null=True, blank=True)
    salary_currency = models.CharField('Валюта', max_length=255, null=True, blank=True)

    description = ''

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Работа'
        unique_together = ('src_alias', 'src_id')

    paginator_related = ['place']
    items_per_page = 15

    def get_absolute_url(self, with_prefix=False, hash_chunk=None):
        return self.url_site

    def link_to_place(self):
        """Связывает запись с местом Place, заполняя атрибут place_id.

        :return:
        """

        # Попробуем найти ранее связанные записи.
        match = self.__class__.objects.filter(
            src_alias=self.src_alias,
            src_place_id=self.src_place_id,
        ).first()

        if match:
            self.place_id = match.place_id
        else:
            # Вычисляем место.
            match = Place.create_place_from_name(self.src_place_name)
            self.place_id = match.id

    @classmethod
    def update_statuses(cls):
        """Обновляет состояния записей по данным внешнего ресурса.

        :return:
        """
        for vacancy in cls.objects.filter(status=cls.STATUS_PUBLISHED):
            manager = cls.MANAGERS.get(vacancy.src_alias)
            if manager:
                archived = manager.get_status(vacancy.url_api)
                if archived:
                    vacancy.save()

    @classmethod
    def fetch_new(cls):
        """Добывает данные из источника и складирует их.

        :return:
        """
        for manager_alias, manager in cls.MANAGERS.items():
            vacancies = manager.fetch_list()
            if not vacancies:
                return

            for vacancy_data in vacancies:
                if vacancy_data.pop('__archived', True):
                    # Архивные пропускаем.
                    continue

                new_vacancy = cls(**vacancy_data)
                new_vacancy.src_alias = manager_alias
                new_vacancy.status = new_vacancy._status_backup = cls.STATUS_PUBLISHED
                new_vacancy.link_to_place()
                try:
                    new_vacancy.save()
                except IntegrityError:
                    pass


class Community(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
                ModelWithCompiledText):
    """Модель сообществ. Формально объединяет некоторую группу людей."""

    place = models.ForeignKey(
        Place, verbose_name='Место', related_name='communities', null=True, blank=True,
        help_text='Для географически локализованных сообществ можно указать место (страна, город, село).<br>'
                  'Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».')

    contacts = models.CharField(
        'Контактные лица', null=True, blank=True, max_length=255,
        help_text=('Контактные лица через запятую, представляющие сообщество, координаторы, основатели.%s' %
                   ModelWithAuthorAndTranslator._hint_userlink))

    url = models.URLField('Страница в сети', null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'

    class Fields:
        title = 'Название сообщества'
        description = {
            'verbose_name': 'Кратко',
            'help_text': ('Сжатая предварительная информация о сообществе (например, направление деятельности). %s' %
                          HINT_IMPERSONAL_REQUIRED)
        }
        text_src = {
            'verbose_name': 'Описание, принципы работы, правила, контактная информация',
            'help_text': '%s' % HINT_IMPERSONAL_REQUIRED,
        }
        linked = {
            'verbose_name': 'Связанные сообщества',
            'help_text': 'Выберите сообщества, имеющие отношение к данному.',
        }
        year = 'Год образования'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.status = self.STATUS_PUBLISHED
        super().save(*args, **kwargs)


class User(RealmBaseModel, AbstractUser):
    """Наша модель пользователей."""

    items_per_page = 100

    objects = UserManager()

    place = models.ForeignKey(
        Place, verbose_name='Место', related_name='users', null=True, blank=True,
        help_text='Место вашего пребывания (страна, город, село).<br>'
                  'Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».')

    # Настрока устарела.
    digest_enabled = models.BooleanField(
        'Получать дайджест', default=True, db_index=True,
        help_text='Включает/отключает еженедельную рассылку с подборкой новых материалов сайта.')

    comments_enabled = models.BooleanField(
        'Разрешить комментарии',
        help_text='Включает/отключает систему комментирования Disqus на страницах ваших публикаций.', default=False)

    disqus_shortname = models.CharField(
        'Идентификатор Disqus', max_length=100, null=True, blank=True,
        help_text='Короткое имя (shortname), под которым вы зарегистрировали форум на Disqus.')

    disqus_category_id = models.CharField(
        'Идентификатор категории Disqus', max_length=30, null=True, blank=True,
        help_text='Если ваш форум на Disqus использует категории, можете указать нужный номер здесь. '
                  'Это не обязательно.')

    timezone = models.CharField(
        'Часовой пояс', max_length=150, null=True, blank=True,
        help_text='Название часового пояса. Например: Asia/Novosibirsk.<br>'
                  '* Устанавливается автоматически в зависимости от места пребывания (см. выше).')

    email_public = models.EmailField(
        'Эл. почта', null=True, blank=True,
        help_text='Адрес электронной почты для показа посетителям сайта.')

    url = models.URLField('Страница в сети', null=True, blank=True)

    class Meta:
        verbose_name = 'Персона'
        verbose_name_plural = 'Люди'

    def set_timezone_from_place(self):
        """Устанавливает временную зону, исходя из места расположения.

        :return:
        """
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
        realm_models = [r.model for r in get_realms().values()]
        bookmarks = FLAG_MODEL.get_flags_for_types(
            realm_models, user=self, status=RealmBaseModel.FLAG_STATUS_BOOKMARK,
            allow_empty=False
        )
        for realm_model, flags in bookmarks.items():
            ids = [flag.object_id for flag in flags]
            items = realm_model.objects.filter(id__in=ids)
            bookmarks[realm_model] = items
        return bookmarks

    def is_deleted(self):
        return not self.is_active

    @classmethod
    def get_actual(cls):
        return cls.objects.filter(is_active=True).order_by('-date_joined').all()

    @classmethod
    def get_paginator_objects(cls):
        return cls.objects.order_by('-date_joined').all()

    @classmethod
    def get_most_voted_objects(cls):
        query = cls.objects.filter(supporters_num__gt=0)
        query = query.select_related('submitter').order_by('-supporters_num')
        return query.all()[:5]

    def get_display_name(self):
        return self.get_full_name() or self.get_username_partial()
    title = property(get_display_name)

    def get_username_partial(self):
        return self.username.split('@')[0]


class Book(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
           ModelWithAuthorAndTranslator, ModelWithPartnerLinks):
    """Модель сущности `Книга`."""

    COVER_UPLOAD_TO = 'books'

    isbn = models.CharField('Код ISBN', max_length=20, unique=True, null=True, blank=True)
    isbn_ebook = models.CharField('Код ISBN эл. книги', max_length=20, unique=True, null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'

    class Fields:
        title = 'Название книги'
        description = {
            'verbose_name': 'Аннотация',
            'help_text': 'Аннотация к книге, или другое краткое описание. %s' % HINT_IMPERSONAL_REQUIRED,
        }
        linked = {
            'verbose_name': 'Связанные книги',
            'help_text': ('Выберите книги, которые имеют отношение к данной. '
                          'Например, для книги-перевода можно указать оригинал.',)
        }
        year = 'Год издания'


class Article(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
              ModelWithCompiledText):
    """Модель сущности `Статья`."""

    LOCATION_INTERNAL = 1
    LOCATION_EXTERNAL = 2

    LOCATIONS = choices_list(
        (LOCATION_INTERNAL, 'На этом сайте'),
        (LOCATION_EXTERNAL, 'На другом сайте'),
    )

    SOURCE_HANDMADE = 1
    SOURCE_SCRAPING = 2
    SOURCE_RSS = 3

    SOURCES = choices_list(
        (SOURCE_HANDMADE, 'Написана на этом сайте'),
        (SOURCE_SCRAPING, 'Соскоблена с другого сайта'),
        (SOURCE_RSS, 'Взята из RSS'),
    )

    source = models.PositiveIntegerField(
        'Тип источника', choices=get_choices(SOURCES), default=SOURCE_HANDMADE,
        help_text='Указывает на механизм, при помощи которого статья появилась на сайте.')

    location = models.PositiveIntegerField(
        'Расположение статьи', choices=get_choices(LOCATIONS), default=LOCATION_INTERNAL,
        help_text='Статью можно написать прямо на этом сайте, либо сформировать статью-ссылку на внешний ресурс.')

    url = models.URLField(
        'URL статьи', null=True, blank=False, unique=True,
        help_text='Внешний URL, по которому доступна статья, которой вы желаете поделиться.')

    published_by_author = models.BooleanField('Я являюсь автором данной статьи', default=True)

    history = HistoricalRecords()

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
            'help_text': ('Выберите статьи, которые имеют отношение к данной. '
                          'Так, например, можно объединить статьи цикла.',)
        }

    def is_handmade(self):
        """Возвращат флаг, указывающий на то, что статья создана на этом сайте.

        :return:
        """
        return self.source == self.SOURCE_HANDMADE

    def update_data_from_url(self, url):
        """Обновляет данные статьи, собирая информация, доступную по указанному URL.

        :param url:
        :return:
        """
        result = scrape_page(url)
        if result is None:
            raise RemoteSourceError('Не удалось получить данные статьи. Проверьте доступность указанного URL.')

        self.title = result['title']
        self.description = result['content_less']
        self.text_src = result['content_more']
        self.source = self.SOURCE_SCRAPING


class Version(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCompiledText):

    current = models.BooleanField('Текущая', default=False, db_index=True)

    class Fields:
        title = 'Номер'
        description = {
            'verbose_name': 'Введение',
            'help_text': 'Краткое описание основных изменений в версии.',
        }
        text_src = {
            'verbose_name': 'Описание',
            'help_text': ('Обзорное, более полное описание нововведений и изменений, произошедших в версии. %s' %
                          HINT_IMPERSONAL_REQUIRED,)
        }

    class Meta:
        verbose_name = 'Версия Python'
        verbose_name_plural = 'Версии Python'
        ordering = ('title',)

    notify_on_publish = False


class Reference(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCompiledText):
    """Модель сущности `Справочник`."""

    TYPE_CHAPTER = 1
    TYPE_PACKAGE = 2
    TYPE_MODULE = 3
    TYPE_FUNCTION = 4
    TYPE_CLASS = 5
    TYPE_METHOD = 6
    TYPE_PROPERTY = 7

    TYPES = choices_list(
        (TYPE_CHAPTER, 'Раздел справки'),
        (TYPE_PACKAGE, 'Описание пакета'),
        (TYPE_MODULE, 'Описание модуля'),
        (TYPE_FUNCTION, 'Описание функции'),
        (TYPE_CLASS, 'Описание класса/типа'),
        (TYPE_METHOD, 'Описание метода класса/типа'),
        (TYPE_PROPERTY, 'Описание свойства класса/типа'),
    )

    type = models.PositiveIntegerField(
        'Тип статьи', choices=get_choices(TYPES), default=TYPE_CHAPTER,
        help_text='Служит для структурирования информации. Справочные статьи разных типов могут выглядеть по-разному.')

    parent = models.ForeignKey(
        'self', related_name='children', verbose_name='Родитель', db_index=True, null=True, blank=True,
        help_text='Укажите родительский раздел. '
                  'Например, для модуля можно указать раздел справки, в которому он относится; '
                  'для метода &#8212; класс.')

    version_added = models.ForeignKey(
        Version, related_name='%(class)s_added', verbose_name='Добавлено в', null=True, blank=True,
        help_text='Версия Python, для которой впервые стала актульна данная статья<br>'
                  '(версия, где впервые появился модуль, пакет, класс, функция).')

    version_deprecated = models.ForeignKey(
        Version, related_name='%(class)s_deprecated', verbose_name='Устарело в', null=True, blank=True,
        help_text='Версия Python, для которой впервые данная статья перестала быть актуальной<br>'
        '(версия, где модуль, пакет, класс, функция были объявлены устаревшими).')

    func_proto = models.CharField(
        'Прототип', max_length=250, null=True, blank=True,
        help_text='Для функций/методов. Описание интерфейса, например: <i>my_func(arg, kwarg=None)</i>')

    func_params = models.TextField(
        'Параметры', null=True, blank=True,
        help_text='Для функций/методов. Описание параметров функции.')

    func_result = models.CharField(
        'Результат', max_length=250, null=True, blank=True,
        help_text='Для функций/методов. Описание результата, например: <i>int</i>.')

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Статья справочника'
        verbose_name_plural = 'Справочник'
        ordering = ('parent_id', 'title')

    class Fields:
        title = {
            'verbose_name': 'Название',
            'help_text': ('Здесь следует указать название раздела справки '
                          'или пакета, модуля, класса, метода, функции и т.п.',)
        }
        description = {
            'verbose_name': 'Кратко',
            'help_text': 'Краткое описание для раздела или пакета, модуля, класса, метода, функции и т.п.',
        }
        text_src = {
            'verbose_name': 'Описание',
            'help_text': 'Подробное описание. Здесь же следует располагать примеры кода.',
        }

    notify_on_publish = False
    autogenerate_slug = True

    def is_type_callable(self):
        return self.type in (self.TYPE_METHOD, self.TYPE_FUNCTION)

    def is_type_method(self):
        return self.type == self.TYPE_METHOD

    def is_type_module(self):
        return self.type == self.TYPE_MODULE

    def is_type_class(self):
        return self.type == self.TYPE_CLASS

    def is_type_chapter(self):
        return self.type == self.TYPE_CHAPTER

    @classmethod
    def get_actual(cls, parent=None, exclude_id=None):
        qs = cls.objects.published()

        if parent is not None:
            qs = qs.filter(parent=parent)

        if exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)

        return qs.order_by('-time_published').all()


class Video(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
            ModelWithAuthorAndTranslator):
    """Модель сущности `Видео`."""

    EMBED_WIDTH = 560
    EMBED_HEIGHT = 315
    COVER_UPLOAD_TO = 'videos'

    code = models.TextField('Код')
    url = models.URLField('URL')

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Видео'
        verbose_name_plural = 'Видео'

    class Fields:
        title = 'Название видео'
        translator = 'Перевод/озвучание'
        description = {
            'help_text': 'Краткое описание того, о чём это видео. %s' % HINT_IMPERSONAL_REQUIRED,
        }
        linked = {
            'verbose_name': 'Связанные видео',
            'help_text': ('Выберите видео, которые имеют отношение к данному. '
                          'Например, можно связать несколько эпизодов видео.',)
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
            raise RemoteSourceError('Не удалось обнаружить ID видео в URL `%s`' % url)

        embed_code = (
            '<iframe src="//player.vimeo.com/video/%s?byline=0&amp;portrait=0&amp;color=ffffff" '
            'width="%s" height="%s" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen>'
            '</iframe>' % (video_id, cls.EMBED_WIDTH, cls.EMBED_HEIGHT))

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
            raise RemoteSourceError('Не удалось обнаружить ID видео в URL `%s`' % url)

        embed_code = (
            '<iframe src="//www.youtube.com/embed/%s?rel=0" '
            'width="%s" height="%s" frameborder="0" allowfullscreen>'
            '</iframe>' % (video_id, cls.EMBED_WIDTH, cls.EMBED_HEIGHT))
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
            raise RemoteSourceError('Не удалось обнаружить обработчик для указанного URL `%s`' % url)

        method_name = 'get_data_from_%s' % hid
        method = getattr(self, method_name, None)
        if method is None:
            raise RemoteSourceError('Не удалось обнаружить метод обработчика URL `%s`' % method_name)

        embed_code, cover_url = method(url)

        self.code = embed_code
        self.update_cover_from_url(cover_url)


class Event(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
            ModelWithCompiledText):
    """Модель сущности `Событие`."""

    SPEC_DEDICATED = 1
    SPEC_HAS_SECTION = 2
    SPEC_HAS_SOME = 3

    SPECS = choices_list(
        (SPEC_DEDICATED, 'Только Python'),
        (SPEC_HAS_SECTION, 'Есть секция/отделение про Python'),
        (SPEC_HAS_SOME, 'Есть упоминания про Python'),
    )

    TYPE_MEETING = 1
    TYPE_CONFERENCE = 2
    TYPE_LECTURE = 3
    TYPE_SPRINT = 4

    TYPES = choices_list(
        (TYPE_MEETING, 'Встреча'),
        (TYPE_LECTURE, 'Лекция'),
        (TYPE_CONFERENCE, 'Конференция'),
        (TYPE_SPRINT, 'Спринт'),
    )

    url = models.URLField('Страница в сети', null=True, blank=True)

    contacts = models.CharField(
        'Контактные лица', null=True, blank=True, max_length=255,
        help_text=('Контактные лица через запятую, координирующие/устраивающие событие.%s' %
                   ModelWithAuthorAndTranslator._hint_userlink))

    place = models.ForeignKey(
        Place, verbose_name='Место', related_name='events', null=True, blank=True,
        help_text=('Укажите место проведения мероприятия.<br><b>Конкретный адрес следует указывать в описании.</b><br>'
                   'Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».'))

    specialization = models.PositiveIntegerField('Специализация', choices=get_choices(SPECS), default=SPEC_DEDICATED)
    type = models.PositiveIntegerField('Тип', choices=get_choices(TYPES), default=TYPE_MEETING)
    time_start = models.DateTimeField('Начало', null=True, blank=True)
    time_finish = models.DateTimeField('Завершение', null=True, blank=True,
                                       help_text='Дату завершения можно и не указывать.')
    fee = models.BooleanField('Участие платное', default=False, db_index=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    class Fields:
        description = {
            'verbose_name': 'Краткое описание',
            'help_text': 'Краткое описание события. %s' % HINT_IMPERSONAL_REQUIRED,
        }
        text_src = {
            'verbose_name': 'Описание, контактная информация',
            'help_text': '%s' % HINT_IMPERSONAL_REQUIRED,
        }
        cover = 'Логотип'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.status = self.STATUS_PUBLISHED
        super().save(*args, **kwargs)

    def get_display_type(self):
        return self.TYPES[self.type]

    def get_display_specialization(self):
        return self.SPECS[self.specialization]

    def is_in_past(self):
        field = self.time_finish or self.time_start
        if field is None:
            return None
        return field < timezone.now()

    def is_now(self):
        if not all([self.time_start, self.time_finish]):
            return False
        return self.time_start <= timezone.now() <= self.time_finish

    @classmethod
    def get_paginator_objects(cls):
        now = timezone.now().date().isoformat()
        # Сначала грядущие в порядке приближения, потом прошедшие.
        return cls.objects.published().extra(
            select={'in_future': "time_start > '%s'" % now}).order_by('-in_future', 'time_start').all()
