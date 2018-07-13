import json
from collections import OrderedDict
from datetime import timedelta
from functools import partial
from itertools import chain

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.db import models, IntegrityError
from django.db.models import Min, Max, Count, Q, F
from django.utils import timezone
from etc.models import InheritedModel
from etc.toolbox import choices_list, get_choices
from simple_history.models import HistoricalRecords
from sitecats.models import ModelWithCategory, Category

from .exceptions import RemoteSourceError
from .generics.models import CommonEntityModel, ModelWithCompiledText, ModelWithAuthorAndTranslator, RealmBaseModel
from .integration.peps import sync as sync_peps
from .integration.resources import PyDigestResource
from .integration.summary import SUMMARY_FETCHERS
from .integration.utils import get_json, scrape_page
from .integration.vacancies import HhVacancyManager
from .utils import format_currency, truncate_chars, UTM, PersonName, sync_many_to_many, get_datetime_from_till

USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')

HINT_IMPERSONAL_REQUIRED = (
    '<strong>Без обозначения личного отношения. Личное отношение можно выразить в Обсуждениях к материалу.</strong>')


if False:  # pragma: nocover
    from .integration.summary.base import ItemsFetcherBase, SummaryItem


class UtmReady:
    """Примесь, добавляющая модели метод для получения URL с метками UTM.

    """

    url_attr = 'url'

    def get_utm_url(self):
        """Возвращает URL с UTM-метками.

        :rtype: str
        """
        return UTM.add_to_external_url(getattr(self, self.url_attr))


class Discussion(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithCategory, ModelWithCompiledText):
    """Модель обсуждений. Пользователи могут обсудить желаемые темы и привязать обсужедние к сущности на сайте.
    Фактически - форум.
    """

    object_id = models.PositiveIntegerField(verbose_name='ID объекта', db_index=True, null=True, blank=True)
    content_type = models.ForeignKey(
        ContentType, verbose_name='Тип содержимого', related_name='%(class)s_discussions', null=True, blank=True,
        on_delete=models.CASCADE)

    linked_object = GenericForeignKey()

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Обсуждение'
        verbose_name_plural = 'Обсуждения'

    class Fields:
        text = 'Обсуждение'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.mark_published()
        super().save(*args, **kwargs)

    def get_description(self):
        return truncate_chars(self.text, 360, html=True)


class ModelWithDiscussions(models.Model):
    """Класс-примесь к моделям сущностей, для который разрешено оставление мнений."""

    discussions = GenericRelation(Discussion)

    class Meta:
        abstract = True


class ExternalResource(UtmReady, RealmBaseModel):
    """Внешние ресурсы. Представляют из себя ссылки на страницы вне сайта."""

    SRC_ALIAS_PYDIGEST = 'pydigest'

    SRC_ALIASES = (
        (SRC_ALIAS_PYDIGEST, 'pythondigest.ru'),
    )

    RESOURCES = OrderedDict([
        (SRC_ALIAS_PYDIGEST, PyDigestResource),
    ])

    src_alias = models.CharField('Идентификатор источника', max_length=20, choices=SRC_ALIASES)
    realm_name = models.CharField('Идентификатор области на pythonz', max_length=20)

    url = models.URLField('Страница ресурса', unique=True)
    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True, default='')

    class Meta:
        verbose_name = 'Внешний ресурс'
        verbose_name_plural = 'Внешние ресурсы'
        ordering = ('-time_created',)

    @classmethod
    def fetch_new(cls):
        """Добывает данные из источников и складирует их.

        :return:
        """
        for resource_alias, resource_cls in cls.RESOURCES.items():
            entries = resource_cls.fetch_entries()
            if not entries:
                return

            added = []
            existing = []
            for entry_data in entries:
                new_resource = cls(**entry_data)
                new_resource.src_alias = resource_alias
                new_resource.mark_published()

                try:
                    new_resource.save()
                    added.append(new_resource.url)
                except IntegrityError:
                    existing.append(new_resource.url)

            if added:
                # Оставляем только те записи, которые до сих пор выдаёт внешний ресурс.
                cls.objects.filter(src_alias=resource_alias).exclude(url__in=chain(added, existing)).delete()


class Summary(RealmBaseModel):
    """Cводки. Ссылки на материалы, собранные с внешних ресурсов."""

    SUMMARY_CATEGORY_ID = 164

    data_items = models.TextField('Элементы сводки')
    data_result = models.TextField('Результат компоновки сводки')

    class Meta:
        verbose_name = 'Сводка'
        verbose_name_plural = 'Сводки'
        ordering = ('-time_created',)

    def __str__(self):
        return '%s' % self.time_created

    @classmethod
    def make_text(cls, fetched):
        """Компонует текст из полученных извне данных.

        :param dict fetched:
        :rtype: str
        """
        summary_text = []

        for fetcher_alias, items in fetched.items():
            if not items:
                continue

            summary_text.append('.. title:: %s' % SUMMARY_FETCHERS[fetcher_alias].title)
            summary_text.append('.. table::')

            for item in items:  # type: SummaryItem
                line = '`%s<%s>`_' % (item.title, item.url)

                if item.description:
                    line += ' — %s' % item.description

                summary_text.append(line)

            summary_text.append('\n')

        if not summary_text:
            return ''

        summary_text.append('')
        summary_text = '\n'.join(summary_text)
        return summary_text

    @classmethod
    def create_article(cls):
        """Создаёт сводку, используя данные, полученные извне.

        :rtype: Summary|None

        """
        summary_text = cls.make_text(cls.fetch())

        format_date = lambda d: d.date().strftime('%d.%m.%Y')
        date_from, date_till = get_datetime_from_till(7)

        robot_id = settings.ROBOT_USER_ID

        article = Article(
            title='Сводка %s — %s' % (format_date(date_from), format_date(date_till)),
            description='А теперь о том, что происходило в последнее время на других ресурсах.',
            submitter_id=robot_id,
            text_src=summary_text,
            source=Article.SOURCE_SCRAPING,
            published_by_author=False,
        )
        article.mark_published()
        article.save()

        article.add_to_category(Category(pk=cls.SUMMARY_CATEGORY_ID), User(pk=robot_id))

        return article

    @classmethod
    def fetch(cls):
        """Добывает данные из источников, складирует их и возвращает в виде словаря."""
        latest = cls.objects.order_by('-pk').first()

        prev_results = json.loads(getattr(latest, 'data_result', '{}'))
        prev_dt = getattr(latest, 'time_created', None)

        all_items = OrderedDict()
        all_results = {}

        for fetcher_alias, fetcher_cls in SUMMARY_FETCHERS.items():
            prev_result = prev_results.get(fetcher_alias) or []
            fetcher = fetcher_cls(previous_result=prev_result, previous_dt=prev_dt)  # type: ItemsFetcherBase
            result = fetcher.run()

            if result is None:
                # По всей видимости, произошла необработанная ошибка.
                items, result = [], prev_result
            else:
                items, result = result

            all_items[fetcher_alias] = items
            all_results[fetcher_alias] = result

        new_summary = cls(data_items=json.dumps(all_items), data_result=json.dumps(all_results))
        new_summary.save()

        return all_items


class PartnerLink(models.Model):
    """Модель партнёрских ссылок. Ссылки могут быть привязаны к любым сущностям сайта.
    Логику формирования и отображения ссылок предоставляют классы из модуля partners.

    """

    object_id = models.PositiveIntegerField(verbose_name='ID объекта', db_index=True)
    content_type = models.ForeignKey(
        ContentType, verbose_name='Тип содержимого', related_name='%(class)s_partner_links',
        on_delete=models.CASCADE)

    partner_alias = models.CharField('Идентфикатор класса партнёра', max_length=50, db_index=True)

    url = models.URLField(
        'Базовая ссылка', help_text='Ссылка на партнёрскую страницу без указания партнёрских данных (идентификатора).')

    description = models.CharField('Описание', max_length=255, null=True, blank=True)

    linked_object = GenericForeignKey()

    class Meta:
        verbose_name = 'Партнёрская ссылка'
        verbose_name_plural = 'Партнёрские ссылки'

    def __str__(self):
        return 'Ссылка %s для %s %s' % (self.id, self.content_type, self.object_id)


class ModelWithPartnerLinks(models.Model):
    """Класс-примесь к моделям сущностей, для который разрешено добавление партнёрских ссылок."""

    partner_links = GenericRelation(PartnerLink)

    class Meta:
        abstract = True


class Place(RealmBaseModel, ModelWithDiscussions):
    """Географическое место. Для людей, событий и пр."""

    details_related = ['last_editor']

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

    def __str__(self):
        return self.geo_title

    def get_pos(self):
        """Возвращает координаты объекта в виде кортежа: (широта, долгота).

        :return:
        """
        lat, lng = self.geo_pos.split('|')
        return lat, lng

    def get_description(self):
        return self.description

    @classmethod
    def create_place_from_name(cls, name):
        """Создаёт место по его имени.

        :param name:
        :return:
        """
        from .integration.utils import get_location_data
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


class Vacancy(UtmReady, RealmBaseModel):

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

    place = models.ForeignKey(
        Place, verbose_name='Место', related_name='vacancies', null=True, blank=True,
        on_delete=models.CASCADE)
    salary_from = models.PositiveIntegerField('Заработная плата', null=True, blank=True)
    salary_till = models.PositiveIntegerField('З/п до', null=True, blank=True)
    salary_currency = models.CharField('Валюта', max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Работа'
        unique_together = ('src_alias', 'src_id')

    paginator_related = ['place']
    items_per_page = 15
    notify_on_publish = False
    url_attr = 'url_site'

    @property
    def cover(self):
        return self.url_logo

    @property
    def description(self):
        # todo Убрать после перевода всего на get_description.
        return self.get_description()

    def get_description(self):
        """Возвращает вычисляемое описание объекта.
        Обычно должен использоваться вместо обращения к атрибуту description,
        которого может не сущестовать у модели.

        """
        chunks = [self.employer_name, self.src_place_name]
        salary_chunk = self.get_salary_str()
        if salary_chunk:
            chunks.append(salary_chunk)
        return ', '.join(chunks)

    @classmethod
    def get_places_stats(cls):
        """Возвращает статистику по количеству вакансий на местах.

        :return:
        """
        stats = list(Place.objects.filter(
            id__in=cls.objects.published().filter(place__isnull=False).distinct().values_list('place_id', flat=True),
            vacancies__status=cls.STATUS_PUBLISHED
        ).annotate(vacancies_count=Count('vacancies')).filter(
            vacancies_count__gt=1
        ).order_by('-vacancies_count', 'title'))

        return stats

    @classmethod
    def get_salary_stats(cls, place=None):
        """Возвращает статистику по зарплатам.

        :param Place|None place: Место, для которого следует получить статистику.
        :return:
        """
        filter_kwargs = {
            'salary_currency__isnull': False,
            'salary_till__isnull': False,
            'salary_from__gt': 900,
        }
        if place is not None:
            filter_kwargs['place'] = place

        stats = list(cls.objects.published().filter(
            **filter_kwargs
        ).values(
            'salary_currency'
        ).annotate(
            min=Min('salary_from'), max=Max('salary_till'), count=Count('id')
        ))

        for stat_row in stats:
            for factor in ('min', 'max'):
                stat_row[factor] = stat_row[factor] or 0

            stat_row['avg'] = stat_row['min'] + ((stat_row['max'] - stat_row['min']) / 2)

            for factor in ('min', 'avg', 'max'):
                stat_row[factor] = format_currency(stat_row[factor])

        return stats

    def get_salary_str(self):
        """Возвращает данные о зарплате в виде строки.

        :return:
        """
        chunks = []
        if self.salary_from:
            chunks.append(format_currency(self.salary_from))

        if self.salary_till:
            chunks.extend(('—', format_currency(self.salary_till)))

        if self.salary_currency:
            chunks.append(self.salary_currency)

        return ' '.join(map(str, chunks)).strip()

    def get_absolute_url(self, with_prefix=False, utm_source=None):
        return self.get_utm_url()

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
        for vacancy in cls.objects.published():
            manager = cls.MANAGERS.get(vacancy.src_alias)
            if manager:
                status = manager.get_status(vacancy.url_api)

                if status:
                    vacancy.status = cls.STATUS_ARCHIVED
                    vacancy.save()

                elif status is None:
                    vacancy.status = cls.STATUS_DELETED
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


class Community(UtmReady, InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
                ModelWithCompiledText):
    """Модель сообществ. Формально объединяет некоторую группу людей."""

    place = models.ForeignKey(
        Place, verbose_name='Место', related_name='communities', null=True, blank=True,
        help_text='Для географически локализованных сообществ можно указать место (страна, город, село).<br>'
                  'Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».',
        on_delete=models.CASCADE)

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
        cover = 'Логотип'
        description = {
            'verbose_name': 'Кратко',
            'help_text': (
                'Сжатая предварительная информация о сообществе (например, направление деятельности). %s' %
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

    @property
    def turbo_content(self):
        return self.text

    def save(self, *args, **kwargs):
        if not self.pk:
            self.mark_published()
        super().save(*args, **kwargs)


class User(UtmReady, RealmBaseModel, AbstractUser):
    """Наша модель пользователей."""

    items_per_page = 14
    details_related = ['last_editor', 'person', 'place']

    objects = UserManager()

    place = models.ForeignKey(
        Place, verbose_name='Место', related_name='users', null=True, blank=True,
        help_text='Место вашего пребывания (страна, город, село).<br>'
                  'Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».',
        on_delete=models.CASCADE)

    profile_public = models.BooleanField(
        'Публичный профиль', default=True, db_index=True,
        help_text='Если выключить, то увидеть ваш профиль сможете только вы.<br>'
                  'В списках пользователей профиль значиться тоже не будет.')

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

    twitter = models.CharField(
        'Twitter', max_length=100, blank=True, default='',
        help_text='Имя в Twitter.')

    url = models.URLField('Страница в сети', null=True, blank=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.get_full_name() or self.get_username_partial()

    @property
    def title(self):
        return self.get_display_name()

    @property
    def is_draft(self):
        # Не считаем черновиком, считаем опубликованным.
        return False

    def set_timezone_from_place(self):
        """Устанавливает временную зону, исходя из места расположения.

        :return:
        """
        if self.place is None:
            self.timezone = None
            return True

        from .integration.utils import get_timezone_name
        lat, lng = self.place.geo_pos.split(',')
        self.timezone = get_timezone_name(lat, lng)

    def get_drafts(self):
        """Возвращает словарь с неопубликованными материалами пользователя.
        Индексирован названиями разделов сайта; значения — списки материалов.

        :rtype: dict
        """
        from .realms import get_realms_models

        drafts = OrderedDict()
        for realm_model in get_realms_models():
            try:
                realm_name = realm_model.get_verbose_name_plural()

            except AttributeError:
                pass

            else:
                items = realm_model.objects.filter(
                    status__in=(self.STATUS_DRAFT, self.STATUS_POSTPONED), submitter_id=self.id
                ).order_by('time_created')

                if items:
                    drafts[realm_name] = items

        return drafts

    def get_stats(self):
        """Возвращает словарь со статистикой пользователя.
        Индексирован названиями разделов сайта; значения — словарь со статистикой:
            cnt_published - кол-во опубликованных материалов
            cnt_postponed - кол-во материалов, назначенных к отложенной публикации

        :rtype: dict
        """
        from .realms import get_realms_models


        stats = OrderedDict()
        for realm_model in get_realms_models():

            try:
                realm_name = realm_model.get_verbose_name_plural()
                cnt_published = realm_model.objects.published().filter(submitter_id=self.id).count()
                cnt_postponed = realm_model.objects.postponed().filter(submitter_id=self.id).count()

            except (FieldError, AttributeError):
                pass

            else:

                if cnt_published or cnt_postponed:
                    stats[realm_name] = {
                        'cnt_published': cnt_published,
                        'cnt_postponed': cnt_postponed,
                    }

        return stats

    def get_bookmarks(self):
        """Возвращает словарь с избранными пользователем элементами (закладками).
        Словарь индексирован классами моделей различных сущностей, в значениях - списки с самими сущностями.

        :rtype: dict
        """
        from siteflags.utils import get_flag_model
        from .realms import get_realms_models

        FLAG_MODEL = get_flag_model()
        bookmarks = FLAG_MODEL.get_flags_for_types(
            get_realms_models(), user=self, status=RealmBaseModel.FLAG_STATUS_BOOKMARK,
            allow_empty=False
        )
        for realm_model, flags in bookmarks.items():
            ids = [flag.object_id for flag in flags]
            items = realm_model.objects.filter(id__in=ids)
            bookmarks[realm_model] = items
        return bookmarks

    @property
    def is_deleted(self):
        return not self.is_active

    @classmethod
    def get_actual(cls):
        return cls.objects.filter(is_active=True, profile_public=True).order_by('-date_joined').all()

    @classmethod
    def get_paginator_objects(cls):
        return cls.get_actual()

    @classmethod
    def get_most_voted_objects(cls, category=None, base_query=None):
        query = cls.objects.filter(supporters_num__gt=0)
        query = query.select_related('submitter').order_by('-supporters_num')
        return query.all()[:5]

    def get_username_partial(self):
        return self.username.split('@')[0]

    def get_description(self):
        """Возвращает вычисляемое описание объекта.
        Обычно должен использоваться вместо обращения к атрибуту description,
        которого может не сущестовать у модели.

        """
        return self.get_display_name()


class PersonsLinked(models.Model):
    """Примесь для моделей, имеющих поля многие-ко-многим, ссылающиеся на Person."""

    persons_fields = []

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_persons_fields()

    def sync_persons_fields(self, known_persons=None):
        if not self.persons_fields:
            return

        if known_persons is None:
            known_persons = Person.get_known_persons()

        for field in self.persons_fields:
            src_field = field.rstrip('s')  # authors - > author
            self._sync_persons(getattr(self, src_field), field, known_persons)

    def _sync_persons(self, names_str, persons_field, known_persons, related_attr='name'):
        names_list = []
        for name in names_str.split(','):
            # Убираем разметку типа [u:1:идле]
            name = name.strip(' []').rpartition(':')[2]
            name and names_list.append(name)

        sync_many_to_many(
            names_list, self, persons_field, related_attr, known_persons,
            unknown_handler=partial(self.create_person, publish=False))

    @classmethod
    def create_person(cls, person_name, known_persons, publish=True):
        """Создаёт персону и добавляет её в словарь известных персон.

        :param str person_name:
        :param dict known_persons:
        :param bool publish:
        :rtype: Person
        """
        person = Person.create(person_name, save=True, publish=publish)
        Person.contribute_to_known_persons(person, known_persons)
        return person


class Book(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
           ModelWithAuthorAndTranslator, ModelWithPartnerLinks, PersonsLinked):
    """Модель сущности `Книга`."""

    COVER_UPLOAD_TO = 'books'

    isbn = models.CharField('ISBN', max_length=20, unique=True, null=True, blank=True)
    isbn_ebook = models.CharField('ISBN эл. книги', max_length=20, unique=True, null=True, blank=True)

    authors = models.ManyToManyField('Person', verbose_name='Авторы', related_name='books', blank=True)

    history = HistoricalRecords()

    persons_fields = ['authors']

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


class Article(UtmReady, InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
              ModelWithCompiledText):
    """Модель сущности `Статья`."""

    LOCATION_INTERNAL = 1
    LOCATION_EXTERNAL = 2

    LOCATIONS = choices_list(
        (LOCATION_INTERNAL, 'На этом сайте'),
        # (LOCATION_EXTERNAL, 'На другом сайте'),
    )

    SOURCE_HANDMADE = 1
    SOURCE_SCRAPING = 2

    SOURCES = choices_list(
        (SOURCE_HANDMADE, 'Написана на этом сайте'),
        (SOURCE_SCRAPING, 'Соскоблена с другого сайта'),
    )

    source = models.PositiveIntegerField(
        'Тип источника', choices=get_choices(SOURCES), default=SOURCE_HANDMADE,
        help_text='Указывает на механизм, при помощи которого статья появилась на сайте.')

    location = models.PositiveIntegerField(
        'Расположение статьи', choices=get_choices(LOCATIONS), default=LOCATION_INTERNAL,
        help_text='Статью можно написать прямо на этом сайте, либо сформировать статью-ссылку на внешний ресурс.')

    url = models.URLField(
        'URL статьи', null=True, blank=True, unique=True,
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
            'help_text': (
                'Выберите статьи, которые имеют отношение к данной. Так, например, можно объединить статьи цикла.',)
        }

    @property
    def turbo_content(self):
        return self.text

    @property
    def is_handmade(self):
        """Возвращат флаг, указывающий на то, что статья создана на этом сайте.

        :return:
        """
        return self.source == self.SOURCE_HANDMADE

    def save(self, *args, **kwargs):

        # Для верного определения уникальности.
        if not self.url:
            self.url = None

        super().save(*args, **kwargs)

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

    current = models.BooleanField('Текущая', default=False)
    date = models.DateField('Дата выпуска')

    class Fields:
        title = {
            'verbose_name': 'Номер',
            'help_text': 'Номер версии с двумя обязательными разрядами и третим опциональным. Например: 2.7.12, 3.6.',
        }
        description = {
            'verbose_name': 'Введение',
            'help_text': 'Краткое описание основных изменений в версии.',
        }
        text_src = {
            'verbose_name': 'Описание',
            'help_text': (
                'Обзорное, более полное описание нововведений и изменений, произошедших в версии. %s' %
                HINT_IMPERSONAL_REQUIRED),
        }

    class Meta:
        verbose_name = 'Версия Python'
        verbose_name_plural = 'Версии Python'
        ordering = ('-date',)

    autogenerate_slug = True
    items_per_page = 10

    def __str__(self):
        return 'Python %s' % self.title

    @property
    def turbo_content(self):
        return self.text

    @classmethod
    def get_paginator_objects(cls):
        qs = super().get_paginator_objects()
        qs = qs.order_by('-date')
        return qs

    @classmethod
    def create_stub(cls, version_number):
        """Создаёт запись о версии, основываясь только на номере.
        Использует для автоматического создания версий, например, из PEP.

        :param str version_number:
        :rtype: Version
        """
        stub = cls(
            title=version_number,
            description='Python версии %s' % version_number,
            text_src='Описание версии ещё не сформировано.',
            submitter_id=settings.ROBOT_USER_ID,
            date=timezone.now().date()
        )
        stub.save()
        return stub


class PEP(RealmBaseModel, CommonEntityModel, ModelWithDiscussions):
    """Предложения по улучшению Питона.

    Заполняются автоматически из репозитория https://github.com/python/peps

    """
    TPL_URL_PYORG = 'https://www.python.org/dev/peps/pep-%s/'

    STATUS_DRAFT = 1
    STATUS_ACTIVE = 2
    STATUS_WITHDRAWN = 3
    STATUS_DEFERRED = 4
    STATUS_REJECTED = 5
    STATUS_ACCEPTED = 6
    STATUS_FINAL = 7
    STATUS_SUPERSEDED = 8
    STATUS_FOOL = 9

    STATUSES = choices_list(
        (STATUS_DRAFT, 'Черновик'),
        (STATUS_ACTIVE, 'Действует'),
        (STATUS_WITHDRAWN, 'Отозвано [автором]'),
        (STATUS_DEFERRED, 'Отложено'),
        (STATUS_REJECTED, 'Отклонено'),
        (STATUS_ACCEPTED, 'Утверждено (принято; возможно не реализовано)'),
        (STATUS_FINAL, 'Финализировано (работа завершена; реализовано)'),
        (STATUS_SUPERSEDED, 'Заменено (имеется более актуальное PEP)'),
        (STATUS_FOOL, 'Розыгрыш на 1 апреля'),
    )

    STATUSES_DEADEND = [STATUS_WITHDRAWN, STATUS_REJECTED, STATUS_SUPERSEDED, STATUS_ACTIVE, STATUS_FOOL, STATUS_FINAL]

    MAP_STATUSES = {
        # (литера, идентификатор_стиля_для_подсветки_строки_таблицы)
        STATUS_DRAFT: ('Черн.', ''),
        STATUS_ACTIVE: ('Действ.', 'success'),
        STATUS_WITHDRAWN: ('Отозв.', 'danger'),
        STATUS_DEFERRED: ('Отл.', ''),
        STATUS_REJECTED: ('Откл.', 'danger'),
        STATUS_ACCEPTED: ('Утв.', 'info'),
        STATUS_FINAL: ('Фин.', 'success'),
        STATUS_SUPERSEDED: ('Зам.', 'warning'),
        STATUS_FOOL: ('Апр.', ''),

    }

    TYPE_PROCESS = 1
    TYPE_STANDARD = 2
    TYPE_INFO = 3

    TYPES = choices_list(
        (TYPE_PROCESS, 'Процесс'),
        (TYPE_STANDARD, 'Стандарт'),
        (TYPE_INFO, 'Информация'),
    )

    # title - перевод заголовка на русский
    # description - английский заголовок
    # slug - номер предложения дополненный нулями до 4х знаков
    # time_published - дата создания PEP

    title = models.CharField('Название', max_length=255)
    num = models.PositiveIntegerField('Номер')
    status = models.PositiveIntegerField('Статус', choices=get_choices(STATUSES), default=STATUS_DRAFT)
    type = models.PositiveIntegerField('Тип', choices=get_choices(TYPES), default=TYPE_STANDARD)

    authors = models.ManyToManyField('Person', verbose_name='Авторы', related_name='peps', blank=True)

    versions = models.ManyToManyField(Version, verbose_name='Версии Питона', related_name='peps', blank=True)
    requires = models.ManyToManyField(
        'self', verbose_name='Зависит от', symmetrical=False, related_name='used_by', blank=True)

    # Следующие два поля кажутся взаимообратными, но пока это не доказано.
    superseded = models.ManyToManyField(
        'self', verbose_name='Заменено на', symmetrical=False, related_name='supersedes', blank=True)
    replaces = models.ManyToManyField(
        'self', verbose_name='Поглощает', symmetrical=False, related_name='replaced_by', blank=True)

    class Meta:
        verbose_name = 'PEP'
        verbose_name_plural = 'PEP'

    def __str__(self):
        return '%s — %s' % (self.slug, self.title)

    autogenerate_slug = True
    items_per_page = 40
    details_related = None

    is_deleted = False
    """Отключаем общую логику работы с удалёнными.
    Здесь у понятия "отозван" своё значение.

    """
    is_draft = False
    """Отключаем общую логику работы с черновиками.
    Здесь у понятия "черновик" своё значение.

    """

    @classmethod
    def get_actual(cls):
        return cls.objects.order_by('-time_published').all()

    def get_link_to_pyorg(self):
        # Получает ссылку на pep в python.org
        return self.TPL_URL_PYORG % self.slug

    def generate_slug(self):
        # Дополняется нулями слева до четырёх знаков.
        return str(self.num).zfill(4)

    @classmethod
    def get_paginator_objects(cls):
        return cls.objects.order_by('num')

    def get_description(self):
        # Русское наименование для показа в рассылке и подобном.
        return self.title

    def mark_published(self):
        """Не использует общий механизм публикации."""

    @classmethod
    def sync_from_repository(cls):
        """Синхронизирует данные в локальной БД с данными репозитория PEP."""
        sync_peps()

    @property
    def bg_class(self):
        return self.MAP_STATUSES[self.status][1]

    @property
    def display_status(self):
        return self.STATUSES[self.status]

    @property
    def display_type(self):
        return self.TYPES[self.type]

    @property
    def display_status_letter(self):
        return self.MAP_STATUSES[self.status][0]

    @property
    def display_type_letter(self):
        return self.TYPES[self.type][0]

    @classmethod
    def find(cls, search_term):
        """Ищет указанный текст в справочнике. Возвращает QuerySet.

        :param str search_term: Строка для поиска.
        :rtype: QuerySet
        """
        return cls.get_actual().filter(
            Q(slug__icontains=search_term) |
            Q(title__icontains=search_term) |
            Q(description__icontains=search_term))


class ReferenceMissing(models.Model):
    """Промахи при поиске в справочнике."""

    term = models.CharField('Термин', max_length=255, unique=True)
    synonyms = models.TextField('Синонимы', blank=True)
    hits = models.PositiveIntegerField('Запросы', default=0)

    class Meta:
        verbose_name = 'Промах справочника'
        verbose_name_plural = 'Промахи справочника'

    def __str__(self):
        return self.term

    @classmethod
    def add(cls, search_term):
        """Добавляет данные по указанному термину в реестр промахов.
        Возвращает True, если была добавлена новая запись.

        :param str search_term: Термин для поиска.
        :rtype: bool
        """
        obj = cls.objects.filter(Q(term__icontains=search_term) | Q(synonyms__icontains=search_term)).first()

        if obj:
            obj.hits += 1
            obj.save()
        else:
            cls(term=search_term, hits=1).save()

        return obj is None


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
                  'для метода &#8212; класс.',
        on_delete=models.CASCADE)

    version_added = models.ForeignKey(
        Version, related_name='%(class)s_added', verbose_name='Добавлено в', null=True, blank=True,
        help_text='Версия Python, для которой впервые стала актульна данная статья<br>'
                  '(версия, где впервые появился модуль, пакет, класс, функция).',
        on_delete = models.CASCADE)

    version_deprecated = models.ForeignKey(
        Version, related_name='%(class)s_deprecated', verbose_name='Устарело в', null=True, blank=True,
        help_text='Версия Python, для которой впервые данная статья перестала быть актуальной<br>'
        '(версия, где модуль, пакет, класс, функция были объявлены устаревшими).',
        on_delete=models.CASCADE)

    func_proto = models.CharField(
        'Прототип', max_length=250, null=True, blank=True,
        help_text='Для функций/методов. Описание интерфейса, например: <i>my_func(arg, kwarg=None)</i>')

    func_params = models.TextField(
        'Параметры', null=True, blank=True,
        help_text='Для функций/методов. Описание параметров функции.')

    func_result = models.CharField(
        'Результат', max_length=250, null=True, blank=True,
        help_text='Для функций/методов. Описание результата, например: <i>int</i>.')

    pep = models.PositiveIntegerField(
        'PEP', null=True, blank=True,
        help_text='Номер предложения по улучшению Питона, связанного с этой статьёй, например: <i>8</i> для PEP-8')

    search_terms = models.CharField(
        'Термины поиска', max_length=500, blank=True, default='',
        help_text='Дополнительные фразы, по которым можно найти данную статью, например: <i>«список», для «list»</i>')

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Статья справочника'
        verbose_name_plural = 'Справочник'
        ordering = ('parent_id', 'title')

    class Fields:
        title = {
            'verbose_name': 'Название',
            'help_text': ('Здесь следует указать название раздела справки '
                          'или пакета, модуля, класса, метода, функции и т.п.')
        }
        description = {
            'verbose_name': 'Кратко',
            'help_text': 'Краткое описание для раздела или пакета, модуля, класса, метода, функции и т.п.',
        }
        text_src = {
            'verbose_name': 'Описание',
            'help_text': 'Подробное описание. Здесь же следует располагать примеры кода.',
        }

    autogenerate_slug = True
    allow_linked = False
    details_related = ['parent', 'submitter']

    @property
    def is_type_callable(self):
        return self.type in (self.TYPE_METHOD, self.TYPE_FUNCTION, self.TYPE_CLASS)

    @property
    def is_type_bundle(self):
        return self.type in (self.TYPE_CHAPTER, self.TYPE_PACKAGE, self.TYPE_MODULE)

    @property
    def is_type_method(self):
        return self.type == self.TYPE_METHOD

    @property
    def is_type_module(self):
        return self.type == self.TYPE_MODULE

    @property
    def is_type_class(self):
        return self.type == self.TYPE_CLASS

    @property
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

    @classmethod
    def find(cls, search_term):
        """Ищет указанный текст в справочнике. Возвращает QuerySet.

        :param str search_term: Строка для поиска.
        :rtype: QuerySet
        """
        return cls.objects.published().filter(
            Q(title__icontains=search_term) | Q(search_terms__icontains=search_term)).order_by('time_published')


class Video(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
            ModelWithAuthorAndTranslator, PersonsLinked):
    """Модель сущности `Видео`."""

    EMBED_WIDTH = 560
    EMBED_HEIGHT = 315
    COVER_UPLOAD_TO = 'videos'

    code = models.TextField('Код')
    url = models.URLField('URL')

    authors = models.ManyToManyField('Person', verbose_name='Авторы', related_name='videos', blank=True)

    history = HistoricalRecords()

    persons_fields = ['authors']

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
            'help_text': (
                'Выберите видео, которые имеют отношение к данному. Например, можно связать несколько эпизодов видео.'),
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

        json = get_json('http://vimeo.com/api/v2/video/%s.json' % video_id)
        cover_url = json[0]['thumbnail_small']

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


class Event(UtmReady, InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
            ModelWithCompiledText):
    """Модель сущности `Событие`."""

    SPEC_DEDICATED = 1
    SPEC_HAS_SECTION = 2
    SPEC_HAS_SOME = 3
    SPEC_MOST = 4

    SPECS = choices_list(
        (SPEC_DEDICATED, 'Только Python'),
        (SPEC_MOST, 'В основном Python'),
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
                   'Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».'),
        on_delete=models.CASCADE)

    specialization = models.PositiveIntegerField('Специализация', choices=get_choices(SPECS), default=SPEC_DEDICATED)
    type = models.PositiveIntegerField('Тип', choices=get_choices(TYPES), default=TYPE_MEETING)
    time_start = models.DateTimeField('Начало', null=True, blank=True)
    time_finish = models.DateTimeField(
        'Завершение', null=True, blank=True,
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
            self.mark_published()
        super().save(*args, **kwargs)

    def get_display_type(self):
        return self.TYPES[self.type]

    def get_display_specialization(self):
        return self.SPECS[self.specialization]

    @property
    def is_in_past(self):
        field = self.time_finish or self.time_start
        if field is None:
            return None
        return field < timezone.now()

    @property
    def is_now(self):
        if not all([self.time_start, self.time_finish]):
            return False
        return self.time_start <= timezone.now() <= self.time_finish

    @property
    def time_forgetmenot(self):
        """Дата напоминания о предстоящем событии (на сутки ранее начала события)."""
        return self.time_start - timedelta(days=1)

    @classmethod
    def get_paginator_objects(cls):
        now = timezone.now()

        # Сначала грядущие в порядке приближения, потом прошедшие в порядке отдалённости.
        qs = cls.objects.published().annotate(
            past=models.Case(
                models.When(time_start__gte=now, then=False),
                models.When(time_start__lt=now, then=True),
                output_field=models.BooleanField(),
            )
        ).annotate(
            gap=models.Case(
                models.When(time_start__gte=now, then=F('time_start') - now),
                models.When(time_start__lt=now, then=now - F('time_start')),
                output_field=models.DurationField(),
            )
        ).order_by('past', 'gap')

        return qs


class Person(UtmReady, InheritedModel, RealmBaseModel, ModelWithCompiledText):
    """Модель сущности `Персона`.

    Персона не обязана являться пользователем сайта, но между этими сущностями может быть связь.

    """
    details_related = ['submitter', 'last_editor', 'user']
    paginator_related = []
    paginator_order = 'name'
    items_per_page = 1000

    user = models.OneToOneField(
        User, verbose_name='Пользователь', related_name='person', null=True, blank=True,
        on_delete=models.CASCADE)
    name = models.CharField('Имя', max_length=90, blank=True)
    name_en = models.CharField('Имя англ.', max_length=90, blank=True)
    aka = models.CharField('Другие имена', max_length=255, blank=True)  # Разделены ;

    class Meta:
        verbose_name = 'Персона'
        verbose_name_plural = 'Персоны'

    class Fields:
        text = {'verbose_name': 'Описание'}
        text_src = {'verbose_name': 'Описание (исх.)'}

    def __str__(self):
        return self.name

    @property
    def title(self):
        return self.get_display_name()

    @classmethod
    def get_known_persons(cls):
        """Возвращает словарь, индексированный именами персон.

        Где значения являются списками с объектами моделей персон.
        Если в списке больше одной модели, значит этому имени соответствует
        несколько разных моделей персон.

        :rtype: dict
        """
        known = {}
        for person in cls.objects.exclude(status=cls.STATUS_DELETED):
            cls.contribute_to_known_persons(person, known_persons=known)
        return known

    @classmethod
    def contribute_to_known_persons(cls, person, known_persons):
        """Добавляет объект указанной персоны в словарь с известными персонами.

        :param Person person:
        :param dict known_persons:
        """
        def add_name(name):
            """Заносит имя в разных вариантах в реестр известных имён.

            :param str name:
            """
            name = PersonName(name)

            for variant in name.get_variants():
                persons_for_variant = known_persons.setdefault(variant, [])
                if person not in persons_for_variant:  # Дубли не нужны.
                    persons_for_variant.append(person)

        add_name(person.name)
        add_name(person.name_en)

        for aka_chunk in person.aka.split(';'):
            add_name(aka_chunk)

    @classmethod
    def find(cls, name):
        """Ищет персону по указанному имени.

        :param str name: Имя для поиска.
        :rtype: models.QuerySet
        """
        return cls.get_actual().filter(
            Q(name__icontains=name) |
            Q(name_en__icontains=name) |
            Q(aka__icontains=name)
        )

    @classmethod
    def create(cls, name, save=False, publish=True):
        """Создаёт объект персоны по имени.

        :param str name:
        :param bool save: Следует ли сохранить объект в БД.
        :param bool publish: Следует ли пометить объект опубликованным.
        :rtype: Person
        """
        person = cls(
            name=name,
            name_en=name,
            status=cls.STATUS_PUBLISHED if publish else cls.STATUS_DRAFT,
            text_src='Описание отсутствует',
            submitter_id=settings.ROBOT_USER_ID,
        )
        if save:
            person.save(notify_published=False, notify_new=False)

        return person

    @classmethod
    def get_paginator_objects(cls):
        persons = super().get_paginator_objects()

        def sort_by_surname(person):
            split = person.name.rsplit(' ', 1)
            name = ' '.join(reversed(split))
            person.name = name
            return name

        result = sorted(persons, key=sort_by_surname)
        return result

    def get_materials(self):
        """Возвращает словарь с матералами, созданными персоной.

        Индексирован названиями разделов сайта; значения — список моделей материалов.

        :rtype: dict
        """
        from .realms import get_realm

        realms = [get_realm('pep'), get_realm('book'), get_realm('video')]  # Пока ограничимся.

        materials = OrderedDict()
        for realm in realms:
            realm_model = realm.model
            realm_name = realm_model.get_verbose_name_plural()

            _, plural = realm.get_names()

            items = getattr(self, plural).order_by('slug', 'title')

            if items:
                materials[realm_name] = (plural, items)

        return materials
