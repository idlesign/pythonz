from enum import unique

from django.db import models
from django.db.models import Q, QuerySet

from ..generics.models import CommonEntityModel, RealmBaseModel
from ..integration.peps import sync as sync_peps
from .discussion import ModelWithDiscussions
from .version import Version


class PEP(RealmBaseModel, CommonEntityModel, ModelWithDiscussions):
    """Предложения по улучшению Питона.

    Заполняются автоматически из репозитория https://github.com/python/peps

    """
    TPL_URL_PYORG: str = 'https://www.python.org/dev/peps/pep-%s/'

    @unique
    class Status(models.IntegerChoices):

        DRAFT = 1, 'Черновик'
        ACTIVE = 2, 'Действует'
        WITHDRAWN = 3, 'Отозвано [автором]'
        DEFERRED = 4, 'Отложено'
        REJECTED = 5, 'Отклонено'
        ACCEPTED = 6, 'Утверждено (принято; возможно не реализовано)'
        FINAL = 7, 'Финализировано (работа завершена; реализовано)'
        SUPERSEDED = 8, 'Заменено (имеется более актуальное PEP)'
        FOOL = 9, 'Розыгрыш на 1 апреля'

    STATUS_MAP = {
        Status.DRAFT: ('Черн.', ''),
        Status.ACTIVE: ('Действ.', 'success'),
        Status.WITHDRAWN: ('Отозв.', 'danger'),
        Status.DEFERRED: ('Отл.', ''),
        Status.REJECTED: ('Откл.', 'danger'),
        Status.ACCEPTED: ('Утв.', 'info'),
        Status.FINAL: ('Фин.', 'success'),
        Status.SUPERSEDED: ('Зам.', 'warning'),
        Status.FOOL: ('Апр.', ''),
    }

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

    slug_pick: bool = True
    slug_auto: bool = True
    items_per_page: int = 40
    details_related: list[str] = []

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

    status = models.PositiveIntegerField('Статус', choices=Status.choices, default=Status.DRAFT)

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
        return f'PEP {self.num} — {self.title}'

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
        return cls.objects.order_by(cls.paginator_order)

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
        return self.STATUS_MAP[self.Status(self.status)][1]

    @property
    def display_status(self) -> str:
        return self.Status(self.status).label

    @property
    def display_status_letter(self) -> str:
        return self.STATUS_MAP[self.Status(self.status)][0]

    @property
    def display_type(self) -> str:
        return self.Type(self.type).label

    @property
    def display_type_letter(self) -> str:
        return self.Type(self.type).label[0]

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
