from enum import unique
from statistics import median
from typing import List, Optional

from django.db import models, IntegrityError
from django.db.models import Count

from .place import Place
from .shared import UtmReady
from ..generics.models import RealmBaseModel
from ..integration.vacancies import HhVacancyManager
from ..utils import format_currency


class Vacancy(UtmReady, RealmBaseModel):

    paginator_related: List[str] = ['place']
    items_per_page: int = 15
    notify_on_publish: bool = False
    url_attr: str = 'url_site'

    @unique
    class Source(models.TextChoices):

        HH = 'hh', 'hh.ru'

    SOURCE_MAP = {
        Source.HH: HhVacancyManager
    }

    src_alias = models.CharField('Идентификатор источника', max_length=20, choices=Source.choices)

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

    @property
    def cover(self) -> str:
        return self.url_logo

    @property
    def description(self) -> str:
        # todo Убрать после перевода всего на get_description.
        return self.get_description()

    def get_description(self) -> str:
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
    def get_places_stats(cls) -> List[Place]:
        """Возвращает статистику по количеству вакансий на местах."""

        stats = list(Place.objects.filter(
            id__in=cls.objects.published().filter(place__isnull=False).distinct().values_list('place_id', flat=True),
            vacancies__status=cls.Status.PUBLISHED

        ).annotate(vacancies_count=Count('vacancies')).filter(
            vacancies_count__gt=2

        ).order_by('-vacancies_count', 'title'))

        return stats

    @classmethod
    def get_salary_stats(cls, place: Optional[Place] = None) -> dict:
        """Возвращает статистику по зарплатам.

        :param place: Место, для которого следует получить статистику.

        """
        filter_kwargs = {
            'salary_currency__isnull': False,
            'salary_till__isnull': False,
            'salary_from__gt': 900,
            'status': cls.Status.PUBLISHED,
        }

        if place is not None:
            filter_kwargs['place'] = place

        stats = list(cls.objects.published().filter(
            **filter_kwargs

        ).values(
            'salary_currency',
            'salary_from',
            'salary_till',
        ))

        by_currency = {}

        for stat_row in stats:

            row = by_currency.setdefault(stat_row['salary_currency'], {
                'min': float('inf'),
                'max': 0,
                'avg': [],
            })

            if row['min'] > stat_row['salary_from']:
                row['min'] = stat_row['salary_from']

            if row['max'] < stat_row['salary_till']:
                row['max'] = stat_row['salary_till']

            if row['max'] < row['min']:
                row['max'] = row['min']

            row['avg'].append(
                row['min'] + ((row['max'] - row['min']) / 2)
            )

        for currency, info in by_currency.items():

            info['avg'] = median(info['avg'])

            for key in {'min', 'max', 'avg'}:
                info[key] = f'{round(info[key] / 1000, 1)}'.replace('.0', '', 1) + 'K'

        return by_currency

    def get_salary_str(self) -> str:
        """Возвращает данные о зарплате в виде строки."""

        chunks = []
        if self.salary_from:
            chunks.append(format_currency(self.salary_from))

        if self.salary_till:
            chunks.extend(('—', format_currency(self.salary_till)))

        if self.salary_currency:
            chunks.append(self.salary_currency)

        return ' '.join(map(str, chunks)).strip()

    def get_absolute_url(self, with_prefix: bool = False, utm_source: str = None) -> str:
        return self.get_utm_url()

    def link_to_place(self):
        """Связывает запись с местом Place, заполняя атрибут place_id."""

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
        """Обновляет состояния записей по данным внешнего ресурса."""

        for_update = []

        for vacancy in cls.objects.published():

            try:
                source = cls.Source(vacancy.src_alias)
                manager = cls.SOURCE_MAP[source]

            except KeyError:
                manager = None

            if not manager:
                continue

            for_update.append(vacancy)

            status = manager.get_status(vacancy.url_api)

            if status:
                vacancy.status = cls.Status.ARCHIVED

            elif status is None:
                vacancy.status = cls.Status.DELETED

        if for_update:
            cls.objects.bulk_update(for_update, fields=['status'])

    @classmethod
    def fetch_new(cls):
        """Добывает данные из источника и складирует их."""

        for manager_alias, manager in cls.SOURCE_MAP.items():
            manager_alias = manager_alias.name

            vacancies = manager.fetch_list()

            if not vacancies:
                return

            for vacancy_data in vacancies:

                if vacancy_data.pop('__archived', True):
                    # Архивные пропускаем.
                    continue

                new_vacancy = cls(**vacancy_data)
                new_vacancy.src_alias = manager_alias
                new_vacancy.status = new_vacancy._status_backup = cls.Status.PUBLISHED
                new_vacancy.link_to_place()

                try:
                    new_vacancy.save()

                except IntegrityError:
                    pass
