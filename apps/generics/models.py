import os
from uuid import uuid4
from contextlib import suppress

from slugify import Slugify, CYRILLIC
from siteflags.models import ModelWithFlag
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import Truncator

from ..utils import UTM, TextCompiler
from ..signals import sig_entity_new, sig_entity_published, sig_support_changed


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')
SLUGIFIER = Slugify(pretranslate=CYRILLIC, to_lower=True, safe_chars='-._', max_length=200)


class ModelWithAuthorAndTranslator(models.Model):
    """Класс-примесь для моделей, требующих поля с автором и переводчиком."""

    _hint_userlink = '<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].'

    author = models.CharField(
        'Автор', max_length=255,
    help_text='Предпочтительно имя и фамилия. Можно указать несколько, разделяя запятыми.%s' % _hint_userlink)

    translator = models.CharField(
        'Перевод', max_length=255, blank=True, null=True,
        help_text=('Укажите переводчиков, если материал переведён на русский с другого языка. '
                   'Если переводчик неизвестен, можно указать главного редактора.%s' % _hint_userlink))

    class Meta:
        abstract = True


class ModelWithCompiledText(models.Model):
    """Класс-примесь для моделей, требующих поля, содержащие тексты в rst."""

    text = models.TextField('Текст')
    text_src = models.TextField('Исходный текст')

    class Meta:
        abstract = True

    @classmethod
    def compile_text(cls, text):
        """Преобразует rst-подобное форматирование в html.

        :param text:
        :return:
        """
        return TextCompiler.compile(text)

    def save(self, *args, **kwargs):
        self.text = self.compile_text(self.text_src)
        super().save(*args, **kwargs)


def get_upload_to(instance, filename):
    """Вычисляет директорию, в которую будет загружена обложка сущности.

    :param instance:
    :param filename:
    :return:
    """
    category = getattr(instance, 'COVER_UPLOAD_TO')
    return os.path.join('img', category, 'orig', '%s%s' % (uuid4(), os.path.splitext(filename)[-1]))


class CommonEntityModel(models.Model):
    """Базовый класс для моделей сущностей."""

    COVER_UPLOAD_TO = 'common'  # Имя категории (оно же имя директории) для хранения загруженных обложек.

    title = models.CharField('Название', max_length=255, unique=True)
    slug = models.CharField('Краткое имя для URL', max_length=200, null=True, blank=True, unique=True)
    description = models.TextField('Описание', blank=False, null=False)
    submitter = models.ForeignKey(USER_MODEL, related_name='%(class)s_submitters', verbose_name='Добавил')
    cover = models.ImageField('Обложка', max_length=255, upload_to=get_upload_to, null=True, blank=True)
    year = models.CharField('Год', max_length=10, null=True, blank=True)

    linked = models.ManyToManyField('self', verbose_name='Связанные объекты', blank=True,
                                    help_text='Выберите объекты, имеющие отношение к данному.')

    class Meta:
        abstract = True

    autogenerate_slug = False
    """Следует ли автоматически генерировать краткое имя в транслите для URL.
    Предполагается, что эта опция также включает машинерию, позволяющую адресовать
    объект по его краткому имени.

    """

    allow_linked = True
    """Разрешена ли привязка элементов друг к другу."""

    def generate_slug(self):
        """Генерирует краткое имя для URL и заполняет им атрибут slug.

        :return:
        """
        return SLUGIFIER(self.title)

    def validate_unique(self, exclude=None):

        # Перекрываем для правильной обработки спарки unique=True и null=True
        # в поле краткого имени URL.

        if not exclude:
            exclude = []

        if not self.slug:
            exclude.append('slug')

        return super().validate_unique(exclude)

    def save(self, *args, **kwargs):
        """Перекрыт, чтобы привести заголовок в порядок.

        :param args:
        :param kwargs:
        :return:
        """
        from ..utils import BasicTypograph

        self.title = BasicTypograph.apply_to(self.title)
        self.description = BasicTypograph.apply_to(self.description)

        if not self.id and self.autogenerate_slug:
            self.slug = self.generate_slug()

        # Требуется для правильной обработки спарки unique=True и null=True
        if not self.slug:
            self.slug = None

        super().save(*args, **kwargs)

    def get_description(self):
        """Возвращает вычисляемое описание объекта.
        Обычно должен использоваться вместо обращения к атрибуту description,
        которого может не сущестовать у модели.

        """
        return self.description

    def update_cover_from_url(self, url):
        """Забирает обложку с указанного URL.

        :param url:
        :return:
        """
        from ..integration.utils import get_image_from_url
        img = get_image_from_url(url)
        self.cover.save(img.name, img, save=False)

    def get_linked(self):
        """Возвращает связанные объекты.

        :return:
        """
        if self.allow_linked:
            return self.linked.all()

        return []

    @classmethod
    def get_paginator_objects(cls):
        """Возвращает выборку объектов для постраничной навигации.
        Должен быть реализован наследниками.

        :return:
        """
        raise NotImplementedError()

    @cached_property
    def get_short_description(self):
        """Возвращает усечённое описание сущности.

        :return:
        """
        return Truncator(self.description).words(25)

    def __str__(self):
        return self.title


class RealmFilteredQuerySet(models.QuerySet):
    """Реализует поддержку запросов с фильтрами для обсластей."""

    def published(self):
        """Возвращает только опубликованные сущности.

        :return:
        """
        return self.filter(status=RealmBaseModel.STATUS_PUBLISHED)

    def postponed(self):
        """Возвращает только сущности, назначенные к отложенной публикации.

        :return:
        """
        return self.filter(status=RealmBaseModel.STATUS_POSTPONED)


class RealmBaseModel(ModelWithFlag):
    """Базовый класс для моделей, использующихся в областях (realms) сайта."""

    STATUS_DRAFT = 1
    STATUS_PUBLISHED = 2
    STATUS_DELETED = 3
    STATUS_ARCHIVED = 4
    STATUS_POSTPONED = 5

    STATUSES = (
        (STATUS_DRAFT, 'Черновик'),
        (STATUS_PUBLISHED, 'Опубликован'),
        (STATUS_POSTPONED, 'К отложенной публикации'),
        (STATUS_DELETED, 'Удален'),
        (STATUS_ARCHIVED, 'В архиве'),
    )

    FLAG_STATUS_BOOKMARK = 1
    """Идентификатор флагов-закладок."""

    FLAG_STATUS_SUPPORT = 2
    """Идентификатор флагов-голосов-поддержки."""

    objects = RealmFilteredQuerySet().as_manager()

    time_created = models.DateTimeField('Дата создания', auto_now_add=True, editable=False)
    time_published = models.DateTimeField('Дата публикации', null=True, editable=False)
    time_modified = models.DateTimeField('Дата редактирования', null=True, editable=False)
    status = models.PositiveIntegerField('Статус', choices=STATUSES, default=STATUS_DRAFT)
    supporters_num = models.PositiveIntegerField('Поддержка', default=0)

    last_editor = models.ForeignKey(
        USER_MODEL, verbose_name='Редактор', related_name='%(class)s_editors', null=True, blank=True,
        help_text='Пользователь, последним отредактировавший объект.')

    class Meta:
        abstract = True

    realm = None
    """Во время исполнения здесь будет объект области (Realm)."""

    edit_form = None
    """Во время исполнения здесь будет форма редактирования."""

    items_per_page = 10
    """Количество объектов для вывода на страницах списков."""

    notify_on_publish = True
    """Следует ли оповещать внешние системы о публикации сущности."""

    paginator_related = ['submitter']
    """Поле, из которого следует тянуть данные одним запросом
    при обращении к постраничному списку объектов.

    """

    details_related = ['submitter', 'last_editor']
    """Поле, из которого следует тянуть данные одним запросом
    при обращении странице с детальной информацией по объекту.

    """

    def mark_published(self):
        """Помечает материал опубликованным."""
        self.status = self.STATUS_PUBLISHED

    def mark_unmodified(self):
        """Используется для того, чтобы при следующем вызове save()
        объекта он не считался изменённым.

        :return:
        """
        self._consider_modified = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._consider_modified = True  # Указывает на то, нужно ли при сохранении устанавливать время изменения
        self._status_backup = self.status

    def save(self, *args, **kwargs):
        """Перекрыт, чтобы можно было отследить флаг модифицированности объекта
        и выставить время модификации соответствующим образом.

        :param args:
        :param kwargs: Среди прочего, поддерживаются:
            notify_published - флаг, указывающий на то, требуется ли отослать
                оповещения о публикации сущности.
        """
        initial_pk = self.pk
        notify_published = kwargs.pop('notify_published', False)

        now = timezone.now()

        if self._status_backup != self.status:
            # Если сохраняем с переходом статуса, наивно полагаем объект немодифицированным.
            self._consider_modified = False
            if self.is_published:
                setattr(self, 'time_published', now)
                notify_published = True

        if self._consider_modified:
            setattr(self, 'time_modified', now)
        else:
            self._consider_modified = True

        super().save(*args, **kwargs)

        with suppress(AttributeError):  # Пропускаем модели, в которых нет нужных атрибутов.
            if not initial_pk and self.pk:
                sig_entity_new.send(self.__class__, entity=self)

        with suppress(AttributeError):  # Пропускаем модели, в которых нет нужных атрибутов.
            notify_published and sig_entity_published.send(self.__class__, entity=self)

    @classmethod
    def get_actual(cls):
        """Возвращает выборку актуальных объектов.

        :return:
        """
        return cls.objects.published().order_by('-time_published').all()

    @classmethod
    def get_paginator_objects(cls):
        """Возвращает выборку для постраничной навигации.

        :return:
        """
        qs = cls.objects.published()
        if cls.paginator_related:
            qs = qs.select_related(*cls.paginator_related)
        qs = qs.order_by('-time_created')

        return qs

    @classmethod
    def cache_get_key_most_voted_objects(cls, category=None, class_name=None):
        """Возвращает ключ кеша, содержащего наиболее популярные материалы раздела.

        :param category:
        :param class_name:
        :return:
        """
        if class_name is None:
            class_name = cls.__name__
        return 'most_voted|%s|%s' % (class_name, category)

    @classmethod
    def get_most_voted_objects(cls, category=None, base_query=None):
        """Возвращает наиболее популярные материалы раздела (и, опционально, категории в нём).

        :param category:
        :param base_query:
        :return:
        """
        cache_key = cls.cache_get_key_most_voted_objects(category=category)
        objects = cache.get(cache_key)

        if objects is None:

            if base_query is None:
                base_query = cls.objects.published()

            query = base_query.filter(supporters_num__gt=0)
            query = query.select_related('submitter').order_by('-supporters_num')
            objects = query.all()[:5]

            cache.set(cache_key, objects, 86400)

        return objects

    @classmethod
    def cache_delete_most_voted_objects(cls, **kwargs):
        """Очищает кеш наиболее популярных материлов раздела.
        :param kwargs:
        :return:
        """
        # TODO Не инвалидирует кеш в категориях раздела. При случае решить, а нужно ли вообще.
        cache.delete(cls.cache_get_key_most_voted_objects(class_name=kwargs['sender']))

    @property
    def is_draft(self):
        """Возвращает булево указывающее на то, является ли сущность черновиком.

        :return:
        """
        return self.status == self.STATUS_DRAFT

    @property
    def is_deleted(self):
        """Возвращает булево указывающее на то, помечена ли сущность удаленной.

        :return:
        """
        return self.status == self.STATUS_DRAFT

    @property
    def is_published(self):
        """Возвращает булево указывающее на то, опубликована ли сущность.

        :return:
        """
        return self.status == self.STATUS_PUBLISHED

    def is_supported_by(self, user):
        """Возвращает указание на то, поддерживает ли данный пользователь данную сущность.

        :param user:
        :return:
        """
        return self.is_flagged(user, status=self.FLAG_STATUS_SUPPORT)

    @classmethod
    def get_category_objects_base_query(cls, category):
        """Возвращает базовый QuerySet выборки объектов в указанной категории.

        :param category:
        :return:
        """
        return cls.get_from_category_qs(category).filter(status=RealmBaseModel.STATUS_PUBLISHED).select_related(
            'submitter')

    @classmethod
    def get_most_voted_objects_in_category(cls, category):
        """Возвращает наиболее популярные объекты из указанной категории.

        :param category:
        :return:
        """
        return cls.get_most_voted_objects(category=category, base_query=cls.get_category_objects_base_query(category))

    @classmethod
    def get_objects_in_category(cls, category):
        """Возвращает объекты из указанной категории.

        :param category:
        :return:
        """
        return cls.get_category_objects_base_query(category).order_by('-time_published')

    def set_support(self, user):
        """Устанавливает флаг поддержки данным пользователем данной сущности.

        :param user:
        :return:
        """
        self.supporters_num += 1
        self.set_flag(user, status=self.FLAG_STATUS_SUPPORT)
        self.mark_unmodified()
        self.save()

        sig_support_changed.send(self.__class__.__name__)

    def remove_support(self, user):
        """Убирает флаг поддержки данным пользователем данной сущности.

        :param user:
        :return:
        """
        self.supporters_num -= 1
        self.remove_flag(user, status=self.FLAG_STATUS_SUPPORT)
        self.mark_unmodified()
        self.save()

        sig_support_changed.send(self.__class__.__name__)

    def get_suppport_for_objects(self, objects_list, user):
        """Возвращает данные о поддержке пользователем(ями) указанного набора сущностей.

        :param objects_list:
        :param user:
        :return:
        """
        return self.get_flags_for_objects(objects_list, user=user)

    def is_bookmarked_by(self, user):
        """Возвращает указание на то, добавил ли данный пользователь данную сущность в избранное.

        :param user:
        :return:
        """
        return self.is_flagged(user, status=self.FLAG_STATUS_BOOKMARK)

    def set_bookmark(self, user):
        """Добавляет данную сущность в избранные для данного пользователя.

        :param user:
        :return:
        """
        self.set_flag(user, status=self.FLAG_STATUS_BOOKMARK)

    def remove_bookmark(self, user):
        """Убирает данную сущность из избранного данного пользователя.

        :param user:
        :return:
        """
        self.remove_flag(user, status=self.FLAG_STATUS_BOOKMARK)

    @classmethod
    def get_verbose_name(cls):
        """Возвращает человекоудобное название типа объекта в ед. числе.

        :return:
        """
        return cls._meta.verbose_name

    @classmethod
    def get_verbose_name_plural(cls):
        """Возвращает человекоудобное название типа объекта во мн. числе.

        :return:
        """
        return cls._meta.verbose_name_plural

    def was_edited(self):
        """Возвращает флаг, указывающий на то, был ли объект отредактирован
        (различаются ли даты создания и редактирования).

        :return:
        """
        format_date = lambda date: date.strftime('%Y%m%d%H%i')
        return self.time_modified and format_date(self.time_modified) != format_date(self.time_created)

    def get_absolute_url(self, with_prefix=False, utm_source=None):
        """Возвращает URL страницы с детальной информацией об объекте.

        :param bool with_prefix: Флаг. Следует ли добавлять название хоста к URL.

        :param None|str utm_source: Строка для создания UTM-метки (Urchin Tracking Module).
            Используются для обозначения источников переходов по URL при сборе статистики посещений.

        :rtype: str
        """
        details_urlname = self.realm.get_details_urlname()

        id_attr = getattr(self, 'slug', None)

        if id_attr:
            details_urlname += '_slug'
        else:
            id_attr = self.id

        url = reverse(details_urlname, args=[str(id_attr)])

        if with_prefix:
            url = '%s%s' % (settings.SITE_URL, url)

        if utm_source is not None:
            url = UTM.add_to_internal_url(url, utm_source)

        return url

    def get_category_absolute_url(self, category):
        """Возвращает URL страницы с разбивкой по данной категории.

        :param category:
        :return:
        """
        tmp, realm_name_plural = self.realm.get_names()
        return reverse('%s:tags' % realm_name_plural, args=[str(category.id)])
