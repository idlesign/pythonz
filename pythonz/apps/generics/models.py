import os
from contextlib import suppress
from copy import copy
from datetime import datetime
from enum import unique
from typing import List, Type
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Model, QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import urlize
from django.utils.text import Truncator
from etc.models import InheritedModelMetaclass
from siteflags.models import ModelWithFlag
from slugify import Slugify, CYRILLIC

from ..integration.base import RemoteSource
from ..integration.utils import get_image_from_url
from ..signals import sig_entity_new, sig_entity_published, sig_support_changed
from ..utils import UTM, TextCompiler, BasicTypograph

USER_MODEL: str = getattr(settings, 'AUTH_USER_MODEL')
SLUGIFIER = Slugify(pretranslate=CYRILLIC, to_lower=True, safe_chars='-._', max_length=200)


if False:  # pragma: nocover
    from .forms import CommonEntityForm  # noqa
    from .realms import RealmBase
    from ..models import Category, User


class ModelWithAuthorAndTranslator(models.Model):
    """Класс-примесь для моделей, требующих поля с автором и переводчиком."""

    _hint_userlink: str = (
        '<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].')

    author = models.CharField(
        'Автор', max_length=255,
        help_text=f'Предпочтительно имя и фамилия. Можно указать несколько, разделяя запятыми.{_hint_userlink}')

    translator = models.CharField(
        'Перевод', max_length=255, blank=True, null=True,
        help_text=('Укажите переводчиков, если материал переведён на русский с другого языка. '
                   f'Если переводчик неизвестен, можно указать главного редактора.{_hint_userlink}'))

    class Meta:
        abstract = True


class ModelWithCompiledText(models.Model):
    """Класс-примесь для моделей, требующих поля, содержащие тексты в rst."""

    text = models.TextField('Текст')
    text_src = models.TextField('Исходный текст')

    class Meta:
        abstract = True

    @classmethod
    def compile_text(cls, text: str) -> str:
        """Преобразует rst-подобное форматирование в html.

        :param text:

        """
        return TextCompiler.compile(text)

    def save(self, *args, **kwargs):
        self.text = self.compile_text(self.text_src)
        super().save(*args, **kwargs)


def get_upload_to(instance: Model, filename: str) -> str:
    """Вычисляет директорию, в которую будет загружена обложка сущности.

    :param instance:
    :param filename:

    """
    category = getattr(instance, 'COVER_UPLOAD_TO')

    return os.path.join('img', category, 'orig', f'{uuid4()}{os.path.splitext(filename)[-1]}')


class CommonEntityModel(models.Model):
    """Базовый класс для моделей сущностей."""

    COVER_UPLOAD_TO = 'common'  # Имя категории (оно же имя директории) для хранения загруженных обложек.

    title = models.CharField('Название', max_length=255)
    slug = models.CharField('Краткое имя для URL', max_length=200, null=True, blank=True, unique=True)
    description = models.TextField('Описание', blank=False, null=False)
    cover = models.ImageField('Обложка', max_length=255, upload_to=get_upload_to, null=True, blank=True)
    year = models.CharField('Год', max_length=10, null=True, blank=True)

    linked = models.ManyToManyField(
        'self', verbose_name='Связанные объекты', blank=True,
        help_text='Выберите объекты, имеющие отношение к данному.')

    class Meta:
        abstract = True

    slug_pick: bool = False
    """Дозволено ли обращение к записям по их краткому имени."""

    slug_auto: bool = False
    """Следует ли автоматически генерировать краткое имя в транслите для URL.
    Предполагается, что эта опция также включает машинерию, позволяющую адресовать
    объект по его краткому имени.

    """

    allow_linked: bool = True
    """Разрешена ли привязка элементов друг к другу."""

    def generate_slug(self) -> str:
        """Генерирует краткое имя для URL и заполняет им атрибут slug."""
        return SLUGIFIER(self.title)

    def validate_unique(self, exclude: List = None):

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

        """
        self.title = BasicTypograph.apply_to(self.title)
        self.description = BasicTypograph.apply_to(self.description)

        if not self.id and self.slug_auto:
            self.slug = self.generate_slug()

        # Требуется для правильной обработки спарки unique=True и null=True
        if not self.slug:
            self.slug = None

        super().save(*args, **kwargs)

    def get_description(self) -> str:
        """Возвращает вычисляемое описание объекта.
        Обычно должен использоваться вместо обращения к атрибуту description,
        которого может не сущестовать у модели.

        """
        return self.description

    def update_cover_from_url(self, url: str):
        """Забирает обложку с указанного URL.

        :param url:

        """
        if '.svg' in url:
            # todo PIL не умеет работать с вектором. Не будем пытаться.
            # Наивно орентируемся на наличие расширения в целях экономии ресурсов.
            return

        img = get_image_from_url(url)

        if img is not None:
            self.cover.save(img.name, img, save=False)

    def get_linked(self) -> QuerySet:
        """Возвращает связанные объекты."""

        if self.allow_linked:
            return self.linked.all()

        return QuerySet(self.__class__).none()

    @classmethod
    def get_paginator_objects(cls) -> QuerySet:
        """Возвращает выборку объектов для постраничной навигации.
        Должен быть реализован наследниками.

        """
        raise NotImplementedError  # pragma: nocover

    @cached_property
    def get_short_description(self) -> str:
        """Возвращает усечённое описание сущности."""
        return Truncator(self.description).words(25)

    def __str__(self) -> str:
        return self.title


class RealmFilteredQuerySet(models.QuerySet):
    """Реализует поддержку запросов с фильтрами для обсластей."""

    def published(self) -> QuerySet:
        """Возвращает только опубликованные сущности."""
        return self.filter(status=RealmBaseModel.Status.PUBLISHED)

    def postponed(self) -> QuerySet:
        """Возвращает только сущности, назначенные к отложенной публикации."""
        return self.filter(status=RealmBaseModel.Status.POSTPONED)


class RealmBaseModel(ModelWithFlag):
    """Базовый класс для моделей, использующихся в областях (realms) сайта."""

    @unique
    class Status(models.IntegerChoices):

        DRAFT = 1, 'Черновик'
        PUBLISHED = 2, 'Опубликован'
        DELETED = 3, 'Удален'
        ARCHIVED = 4, 'В архиве'
        POSTPONED = 5, 'К отложенной публикации'

    FLAG_STATUS_BOOKMARK = 1
    """Идентификатор флагов-закладок."""

    FLAG_STATUS_SUPPORT = 2
    """Идентификатор флагов-голосов-поддержки."""

    objects = RealmFilteredQuerySet().as_manager()

    time_created = models.DateTimeField('Дата создания', auto_now_add=True, editable=False)
    time_published = models.DateTimeField('Дата публикации', null=True, editable=False)
    time_modified = models.DateTimeField('Дата редактирования', null=True, editable=False)
    status = models.PositiveIntegerField('Статус', choices=Status.choices, default=Status.DRAFT)
    supporters_num = models.PositiveIntegerField('Поддержка', default=0)

    submitter = models.ForeignKey(
        USER_MODEL, verbose_name='Добавил', related_name='%(class)s_submitters', default=settings.ROBOT_USER_ID,
        on_delete=models.SET_DEFAULT)
    last_editor = models.ForeignKey(
        USER_MODEL, verbose_name='Редактор', related_name='%(class)s_editors', null=True, blank=True,
        help_text='Пользователь, последним отредактировавший объект.', default=settings.ROBOT_USER_ID, 
        on_delete=models.SET_DEFAULT,)

    class Meta:
        abstract = True

    realm: 'RealmBase' = None
    """Во время исполнения здесь будет объект области (Realm)."""

    edit_form: 'CommonEntityForm' = None
    """Во время исполнения здесь будет форма редактирования."""

    items_per_page: int = 10
    """Количество объектов для вывода на страницах списков."""

    notify_on_publish: bool = True
    """Следует ли оповещать внешние системы о публикации сущности."""

    allow_edit_anybody: bool = True
    """Дозволено редактирования любому пользователю (не автору)."""

    allow_edit_published: bool = False
    """Дозволено редактирования опубликованных материалов."""

    paginator_order: str = '-time_created'
    """Поле, по которому следует сортировать объекты
    при обращении к постраничному списку.

    """

    paginator_related: List[str] = ['submitter']
    """Поле, из которого следует тянуть данные одним запросом
    при обращении к постраничному списку объектов.

    """

    details_related: List[str] = ['submitter', 'last_editor']
    """Поле, из которого следует тянуть данные одним запросом
    при обращении странице с детальной информацией по объекту.

    """

    @classmethod
    def make_html(cls, text: str) -> str:
        """Применяет базовую html-разметку к указанному тексту.

        :param text:

        """
        return urlize(text.replace('\n', '<br />'), nofollow=True)

    def mark_published(self):
        """Помечает материал опубликованным."""
        self.status = self.Status.PUBLISHED
        self._consider_published = True

    def mark_unmodified(self):
        """Используется для того, чтобы при следующем вызове save()
        объекта он не считался изменённым.

        """
        self._consider_modified = False

    @property
    def turbo_content(self) -> str:
        return ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._consider_published = False
        """Указывает на то, следует ли считать сущность опубликованной."""

        self._consider_modified = True
        """Указывает на то, нужно ли при сохранении устанавливать время изменения"""

        self._status_backup = self.status

    def on_publish(self):
        """Вызывается при смене стутуса на «Опубликовано»."""

    def save(self, *args, **kwargs):
        """Перекрыт, чтобы можно было отследить флаг модифицированности объекта
        и выставить время модификации соответствующим образом.

        :param args:

        :param kwargs: Среди прочего, поддерживаются:

            notify_published - флаг, указывающий на то, требуется ли отослать
                оповещения о публикации сущности.

            notify_new - флаг, указывающий на то, требуется ли отослать
                оповещения о создании сущности.
        """
        initial_pk = self.pk
        notify_published = kwargs.pop('notify_published', None)
        notify_new = kwargs.pop('notify_new', True)

        now = timezone.now()

        status_changed = self._status_backup != self.status

        if status_changed or self._consider_published:

            if status_changed:
                # Если сохраняем с переходом статуса, наивно полагаем объект немодифицированным.
                self._consider_modified = False

                if self.is_published:
                    self.on_publish()

            if self.is_published:
                setattr(self, 'time_published', now)
                self._consider_published = False

                if notify_published is None:
                    notify_published = True

        if self._consider_modified:
            setattr(self, 'time_modified', now)

        else:
            self._consider_modified = True

        super().save(*args, **kwargs)

        with suppress(AttributeError):  # Пропускаем модели, в которых нет нужных атрибутов.

            if notify_new and (not initial_pk and self.pk):
                sig_entity_new.send(self.__class__, entity=self)

        with suppress(AttributeError):  # Пропускаем модели, в которых нет нужных атрибутов.
            notify_published and sig_entity_published.send(self.__class__, entity=self)

    @classmethod
    def find(cls, *search_terms: str) -> QuerySet:
        """Ищет указанный текст в данных модели. Возвращает QuerySet.

        :param search_terms: Строки для поиска.

        """
        raise NotImplementedError  # pragma: nocover

    @classmethod
    def get_actual(cls, **kwargs) -> QuerySet:
        """Возвращает выборку актуальных объектов."""
        return cls.objects.published().order_by('-time_published').all()

    @classmethod
    def get_paginator_objects(cls) -> QuerySet:
        """Возвращает выборку для постраничной навигации."""

        qs = cls.objects.published()

        if cls.paginator_related:
            qs = qs.select_related(*cls.paginator_related)

        qs = qs.order_by(cls.paginator_order)

        return qs

    @classmethod
    def cache_get_key_most_voted_objects(cls, category: 'Category' = None, class_name: str = None) -> str:
        """Возвращает ключ кеша, содержащего наиболее популярные материалы раздела.

        :param category:
        :param class_name:

        """
        if class_name is None:
            class_name = cls.__name__

        return f'most_voted|{class_name}|{category}'

    @classmethod
    def get_most_voted_objects(cls, category: 'Category' = None, base_query: QuerySet = None) -> QuerySet:
        """Возвращает наиболее популярные материалы раздела (и, опционально, категории в нём).

        :param category:
        :param base_query:

        """
        cache_key = cls.cache_get_key_most_voted_objects(category=category)
        objects = cache.get(cache_key)

        if objects is None:

            if base_query is None:
                base_query = cls.objects.published()

            query = base_query.filter(supporters_num__gt=0)

            if cls.paginator_related:
                query = query.select_related(*cls.paginator_related)

            query = query.order_by('-supporters_num')
            objects = query.all()[:3]

            cache.set(cache_key, objects, 86400)

        return objects

    @classmethod
    def cache_delete_most_voted_objects(cls, **kwargs):
        """Очищает кеш наиболее популярных материлов раздела.

        :param kwargs:

        """
        # TODO Не инвалидирует кеш в категориях раздела. При случае решить, а нужно ли вообще.
        cache.delete(cls.cache_get_key_most_voted_objects(class_name=kwargs['sender']))

    @property
    def is_draft(self) -> bool:
        """Возвращает булево указывающее на то, является ли сущность черновиком."""
        return self.status == self.Status.DRAFT

    @property
    def is_deleted(self) -> bool:
        """Возвращает булево указывающее на то, помечена ли сущность удаленной."""
        return self.status == self.Status.DELETED

    @property
    def is_published(self) -> bool:
        """Возвращает булево указывающее на то, опубликована ли сущность."""
        return self.status == self.Status.PUBLISHED

    def is_supported_by(self, user: 'User') -> bool:
        """Возвращает указание на то, поддерживает ли данный пользователь данную сущность.

        :param user:

        """
        return self.is_flagged(user, status=self.FLAG_STATUS_SUPPORT)

    @classmethod
    def get_category_objects_base_query(cls, category: 'Category') -> QuerySet:
        """Возвращает базовый QuerySet выборки объектов в указанной категории.

        :param category:

        """
        return cls.get_from_category_qs(  # ModelWithCategory
            category
        ).filter(status=RealmBaseModel.Status.PUBLISHED).select_related('submitter')

    @classmethod
    def get_most_voted_objects_in_category(cls, category: 'Category') -> QuerySet:
        """Возвращает наиболее популярные объекты из указанной категории.

        :param category:

        """
        return cls.get_most_voted_objects(category=category, base_query=cls.get_category_objects_base_query(category))

    @classmethod
    def get_objects_in_category(cls, category: 'Category') -> QuerySet:
        """Возвращает объекты из указанной категории.

        :param category:

        """
        return cls.get_category_objects_base_query(category).order_by('-time_published')

    def set_support(self, user: 'User'):
        """Устанавливает флаг поддержки данным пользователем данной сущности.

        :param user:

        """
        self.supporters_num += 1
        self.set_flag(user, status=self.FLAG_STATUS_SUPPORT)
        self.mark_unmodified()
        self.save()

        sig_support_changed.send(self.__class__.__name__)

    def remove_support(self, user: 'User'):
        """Убирает флаг поддержки данным пользователем данной сущности.

        :param user:

        """
        self.supporters_num -= 1
        self.remove_flag(user, status=self.FLAG_STATUS_SUPPORT)
        self.mark_unmodified()
        self.save()

        sig_support_changed.send(self.__class__.__name__)

    def get_suppport_for_objects(self, objects_list: QuerySet, user: 'User') -> dict:
        """Возвращает данные о поддержке пользователем(ями) указанного набора сущностей.

        :param objects_list:
        :param user:

        """
        return self.get_flags_for_objects(objects_list, user=user)

    def is_bookmarked_by(self, user: 'User') -> bool:
        """Возвращает указание на то, добавил ли данный пользователь данную сущность в избранное.

        :param user:

        """
        return self.is_flagged(user, status=self.FLAG_STATUS_BOOKMARK)

    def set_bookmark(self, user: 'User'):
        """Добавляет данную сущность в избранные для данного пользователя.

        :param user:

        """
        self.set_flag(user, status=self.FLAG_STATUS_BOOKMARK)

    def remove_bookmark(self, user: 'User'):
        """Убирает данную сущность из избранного данного пользователя.

        :param user:

        """
        self.remove_flag(user, status=self.FLAG_STATUS_BOOKMARK)

    @classmethod
    def get_verbose_name(cls) -> str:
        """Возвращает человекоудобное название типа объекта в ед. числе."""
        return cls._meta.verbose_name

    @classmethod
    def get_verbose_name_plural(cls) -> str:
        """Возвращает человекоудобное название типа объекта во мн. числе."""
        return cls._meta.verbose_name_plural

    def was_edited(self) -> bool:
        """Возвращает флаг, указывающий на то, был ли объект отредактирован
        (различаются ли даты создания и редактирования).

        """

        def format_date(date: datetime):
            return date.strftime('%Y%m%d%H%i')

        return self.time_modified and format_date(self.time_modified) != format_date(self.time_created)

    def get_absolute_url(self, with_prefix: bool = False, utm_source: str = None) -> str:
        """Возвращает URL страницы с детальной информацией об объекте.

        :param with_prefix: Флаг. Следует ли добавлять название хоста к URL.

        :param utm_source: Строка для создания UTM-метки (Urchin Tracking Module).
            Используются для обозначения источников переходов по URL при сборе статистики посещений.

        """
        details_urlname = self.realm.get_details_urlname()

        id_attr = getattr(self, 'slug', None)

        if id_attr:
            details_urlname += '_slug'

        else:
            id_attr = self.id

        url = reverse(details_urlname, args=[str(id_attr)])

        if with_prefix:
            url = f'{settings.SITE_URL}{url}'

        if utm_source is not None:
            url = UTM.add_to_internal_url(url, utm_source)

        return url

    @property
    def absolute_url_prefixed(self) -> str:
        return self.get_absolute_url(with_prefix=True)

    def get_category_absolute_url(self, category: 'Category') -> str:
        """Возвращает URL страницы с разбивкой по данной категории.

        :param category:

        """
        tmp, realm_name_plural = self.realm.get_names()

        return reverse(f'{realm_name_plural}:tags', args=[str(category.id)])

    def get_display_name(self) -> str:
        """Имя для отображения в интерфейсе."""
        return self.__str__()


class WithRemoteSourceMeta(InheritedModelMetaclass):

    def __new__(cls, name, bases, attrs, **kwargs):
        source_group = attrs.get('source_group')

        if source_group:
            # Прописываем choices для источников.
            src_alias = copy(bases[-1].src_alias.field)
            src_alias.choices = source_group.get_enum().choices
            attrs['src_alias'] = src_alias

        cls_new = super().__new__(cls, name, bases, attrs, **kwargs)

        if source_group:
            # Прописываем уникальность.
            cls_new._meta.unique_together = (('src_alias', 'src_id'),)

        return cls_new


class WithRemoteSource(RealmBaseModel, metaclass=WithRemoteSourceMeta):
    """Примесь для моделей, умеющих хранить данные, полученные из внешних источников."""

    source_group: Type[RemoteSource] = None

    # Ограничения (choices) выбора источников проставляются в метаклассе.
    src_alias = models.CharField('Идентификатор источника', max_length=20, null=True, blank=True)
    src_id = models.CharField('ID в источнике', max_length=50, null=True, blank=True)

    url = models.URLField('Страница в сети', null=True, blank=True)

    class Meta:

        abstract = True
        unique_together = ('src_alias', 'src_id')  # Не наследуется https://code.djangoproject.com/ticket/16732

    def extract_page_info(self):
        """Возвращает информацию о странице, расположенной
        по указанному в объекте URL, либо None.

        """
        source = self.source_group.get_source(self.src_alias)
        info = source.get_page_info(self.url)
        return info

    @classmethod
    def spawn_object(cls, item_data: dict, *, source: RemoteSource):
        """Конструирует объект модели, наполняя данными из словаря.

        :param item_data:
        :param source: Объект источника.

        """
        obj = cls(**item_data)
        obj.src_alias = source.alias
        obj.status = obj._status_backup = cls.Status.PUBLISHED

        return obj

    @classmethod
    def fetch_items(cls):
        """Добывает данные из источника и складирует их."""

        for _, source in cls.source_group.get_sources().items():

            source_obj = source()
            items = source_obj.fetch_list()

            if not items:
                return

            seen = set(cls.objects.filter(

                src_alias=source.alias,
                src_id__in=[item_data['src_id'] for item_data in items],

            ).values_list('src_id', flat=True))

            for item_data in items:

                if item_data['src_id'] in seen:
                    continue

                obj = cls.spawn_object(item_data, source=source_obj)

                # По одному, чтобы отработала логика save().
                obj.save(notify_published=False)
