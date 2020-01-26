from typing import List

from django.db import models
from django.db.models import Q, QuerySet
from etc.toolbox import choices_list, get_choices

from .discussion import ModelWithDiscussions
from .version import Version
from ..generics.models import CommonEntityModel, RealmBaseModel
from ..integration.peps import sync as sync_peps


class PEP(RealmBaseModel, CommonEntityModel, ModelWithDiscussions):
    """Предложения по улучшению Питона.

    Заполняются автоматически из репозитория https://github.com/python/peps

    """
    TPL_URL_PYORG: str = 'https://www.python.org/dev/peps/pep-%s/'

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

    autogenerate_slug: bool = True
    items_per_page: int = 40
    details_related: List[str] = []

    is_deleted: bool = False
    """Отключаем общую логику работы с удалёнными.
    Здесь у понятия "отозван" своё значение.

    """
    is_draft: bool = False
    """Отключаем общую логику работы с черновиками.
    Здесь у понятия "черновик" своё значение.

    """

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
        return f'{self.slug} — {self.title}'

    @property
    def turbo_content(self) -> str:
        return self.title

    @classmethod
    def get_actual(cls) -> QuerySet:
        return cls.objects.order_by('-time_published').all()

    def get_link_to_pyorg(self) -> str:
        # Получает ссылку на pep в python.org
        return self.TPL_URL_PYORG % self.slug

    def generate_slug(self) -> str:
        # Дополняется нулями слева до четырёх знаков.
        return str(self.num).zfill(4)

    @classmethod
    def get_paginator_objects(cls) -> QuerySet:
        return cls.objects.order_by('num')

    def get_description(self) -> str:
        # Русское наименование для показа в рассылке и подобном.
        return self.title

    def mark_published(self):
        """Не использует общий механизм публикации."""

    @classmethod
    def sync_from_repository(cls):
        """Синхронизирует данные в локальной БД с данными репозитория PEP."""
        sync_peps()

    @property
    def bg_class(self) -> str:
        return self.MAP_STATUSES[self.status][1]

    @property
    def display_status(self) -> str:
        return self.STATUSES[self.status]

    @property
    def display_type(self) -> str:
        return self.TYPES[self.type]

    @property
    def display_status_letter(self) -> str:
        return self.MAP_STATUSES[self.status][0]

    @property
    def display_type_letter(self) -> str:
        return self.TYPES[self.type][0]

    @classmethod
    def find(cls, *search_terms: str) -> QuerySet:
        """Ищет указанный текст в справочнике. Возвращает QuerySet.

        :param search_terms: Строка для поиска.

        """
        q = Q()

        for term in search_terms:

            if not term:
                continue

            q |= Q(slug__icontains=term) | Q(title__icontains=term) | Q(description__icontains=term)

        return cls.get_actual().filter(q)
