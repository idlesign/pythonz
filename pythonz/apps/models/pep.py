from enum import Enum, unique
from typing import List

from django.db import models
from django.db.models import Q, QuerySet
from etc.choices import ChoicesEnumMixin
from etc.toolbox import get_choices

from .discussion import ModelWithDiscussions
from .version import Version
from ..generics.models import CommonEntityModel, RealmBaseModel
from ..integration.peps import sync as sync_peps


class PEP(RealmBaseModel, CommonEntityModel, ModelWithDiscussions):
    """Предложения по улучшению Питона.

    Заполняются автоматически из репозитория https://github.com/python/peps

    """
    TPL_URL_PYORG: str = 'https://www.python.org/dev/peps/pep-%s/'

    @unique
    class Status(ChoicesEnumMixin, Enum):

        DRAFT = 1, 'Черновик', ('Черн.', '')
        ACTIVE = 2, 'Действует', ('Действ.', 'success')
        WITHDRAWN = 3, 'Отозвано [автором]', ('Отозв.', 'danger')
        DEFERRED = 4, 'Отложено', ('Отл.', '')
        REJECTED = 5, 'Отклонено', ('Откл.', 'danger')
        ACCEPTED = 6, 'Утверждено (принято; возможно не реализовано)', ('Утв.', 'info')
        FINAL = 7, 'Финализировано (работа завершена; реализовано)', ('Фин.', 'success')
        SUPERSEDED = 8, 'Заменено (имеется более актуальное PEP)', ('Зам.', 'warning')
        FOOL = 9, 'Розыгрыш на 1 апреля', ('Апр.', '')

    STATUSES_DEADEND = [
        Status.WITHDRAWN,
        Status.REJECTED,
        Status.SUPERSEDED,
        Status.ACTIVE,
        Status.FOOL,
        Status.FINAL
    ]

    @unique
    class Type(models.IntegerChoices):

        PROCESS = 1, 'Процесс'
        STANDARD = 2, 'Стандарт'
        INFO = 3, 'Информация'

    autogenerate_slug: bool = True
    items_per_page: int = 40
    details_related: List[str] = []

    # Далее отключаем общую логику работы с удалёнными.
    is_published: bool = True
    is_deleted: bool = False
    is_draft: bool = False

    # title - перевод заголовка на русский
    # description - английский заголовок
    # slug - номер предложения дополненный нулями до 4х знаков
    # time_published - дата создания PEP

    title = models.CharField('Название', max_length=255)

    num = models.PositiveIntegerField('Номер')

    status = models.PositiveIntegerField('Статус', choices=get_choices(Status), default=Status.DRAFT)

    type = models.PositiveIntegerField('Тип', choices=Type.choices, default=Type.STANDARD)

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
        return self.Status.get_hint(self.status)[1]

    @property
    def display_status(self) -> str:
        return self.Status.get_title(self.status)

    @property
    def display_status_letter(self) -> str:
        return self.Status.get_hint(self.status)[0]

    @property
    def display_type(self) -> str:
        return self.Type.labels[self.type]

    @property
    def display_type_letter(self) -> str:
        return self.Type.labels[self.type][0]

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
