"""Единый поиск по сайту.

Области поиска задаются декларативно атрибутами `search_weight_fields`
и `search_exact_fields` классов областей (realms). Механизм поиска выбирается
автоматически по типу подключения к базе данных: для PostgreSQL задействуется
полнотекстовый поиск с морфологией и ранжированием, для прочих баз — простой
переносимый поиск по вхождению подстроки.

"""
from dataclasses import dataclass

from django.db import connection, models
from django.db.models import Case, IntegerField, Q, QuerySet, Value, When

from .utils import swap_layout

RESULTS_LIMIT: int = 50
"""Максимальное число результатов из одной области поиска."""

RANK_MIN: float = 0.01
"""Минимальный ранг результата полнотекстового поиска."""


@dataclass(frozen=True)
class SearchArea:
    """Область поиска: модель и правила поиска по её полям."""

    model: type[models.Model]
    """Модель, по объектам которой ведётся поиск."""

    title: str
    """Название области для группировки результатов."""

    weight_fields: tuple[tuple[str, str], ...]
    """Поля для поиска и их веса (A — наиболее значимые, D — наименее)."""

    exact_fields: tuple[str, ...] = ()
    """Поля, по которым проверяется точное совпадение с запросом."""

    def get_queryset(self) -> QuerySet:
        """Возвращает базовую выборку области (актуальные объекты)."""
        get_actual = getattr(self.model, 'get_actual', None)
        return get_actual() if get_actual is not None else self.model.objects.all()


@dataclass
class AreaResults:
    """Результаты поиска по одной области."""

    area: SearchArea
    """Область поиска."""

    results: list[models.Model]
    """Найденные объекты, отсортированные по убыванию релевантности."""


@dataclass
class SearchResults:
    """Сводные результаты поиска по всем областям."""

    term: str
    """Обработанный поисковый запрос."""

    groups: list[AreaResults]
    """Непустые результаты, сгруппированные по областям."""

    @property
    def total(self) -> int:
        """Общее количество найденных объектов."""
        return sum(len(group.results) for group in self.groups)


def get_areas() -> list[SearchArea]:
    """Возвращает области поиска, собранные из декларативных атрибутов областей сайта."""
    from .realms import get_realms  # noqa: PLC0415 во избежание циклического импорта

    return [
        SearchArea(
            model=realm.model,
            title=realm.model._meta.verbose_name_plural,
            weight_fields=realm.search_weight_fields,
            exact_fields=realm.search_exact_fields,
        )
        for realm in get_realms().values()
        if realm.search_weight_fields
    ]


class Backend:
    """Базовый механизм поиска."""

    @classmethod
    def search(cls, area: SearchArea, terms: list[str]) -> QuerySet:
        """Возвращает выборку объектов области, ранжированную по релевантности.

        :param area: Область поиска.
        :param terms: Поисковые термины (включая вариант в другой раскладке).

        """
        raise NotImplementedError


class SimpleBackend(Backend):
    """Переносимый поиск по вхождению подстроки с простым ранжированием."""

    @classmethod
    def search(cls, area: SearchArea, terms: list[str]) -> QuerySet:
        main_field = area.weight_fields[0][0]
        main_term = terms[0]
        query = Q()

        for field_name, _ in area.weight_fields:

            for term in terms:

                if term:
                    query |= Q(**{f'{field_name}__icontains': term})

        rank = Case(
            When(condition=Q(**{f'{main_field}__iexact': main_term}), then=Value(3)),
            When(condition=Q(**{f'{main_field}__istartswith': main_term}), then=Value(2)),
            When(condition=Q(**{f'{main_field}__icontains': main_term}), then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )

        return (
            area.get_queryset()
            .filter(query)
            .annotate(rank=rank)
            .order_by('-rank', '-pk')[:RESULTS_LIMIT]
        )


class PostgresBackend(Backend):
    """Полнотекстовый поиск PostgreSQL с учётом морфологии русского языка."""

    config: str = 'russian'
    """Конфигурация полнотекстового поиска PostgreSQL."""

    @classmethod
    def search(cls, area: SearchArea, terms: list[str]) -> QuerySet:
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector  # noqa: PLC0415

        vectors = [
            SearchVector(field_name, config=cls.config, weight=weight)
            for field_name, weight in area.weight_fields
        ]
        vector = vectors[0]

        for other in vectors[1:]:
            vector += other

        query = None

        for term in terms:

            if not term:
                continue

            search_query = SearchQuery(term, search_type='websearch', config=cls.config)
            query = search_query if query is None else query | search_query

        if query is None:
            return area.model.objects.none()

        return (
            area.get_queryset()
            .annotate(rank=SearchRank(vector, query))
            .filter(rank__gte=RANK_MIN)
            .order_by('-rank', '-pk')[:RESULTS_LIMIT]
        )


def get_backend() -> type[Backend]:
    """Возвращает механизм поиска, соответствующий текущей базе данных."""
    if connection.vendor == 'postgresql':
        return PostgresBackend

    return SimpleBackend


def prepare_terms(term: str) -> tuple[str, list[str]]:
    """Приводит запрос к рабочему виду и дополняет вариантом в другой раскладке.

    :param term: Строка поискового запроса.

    """
    search_term = term.strip(' ()')[:200]
    terms = [search_term]

    if search_term and (swapped := swap_layout(search_term)):
        terms.append(swapped)

    return search_term, terms


def search_areas(term: str) -> SearchResults:
    """Ищет указанный термин во всех областях поиска.

    :param term: Строка поискового запроса.

    """
    search_term, terms = prepare_terms(term)

    if not search_term:
        return SearchResults(term='', groups=[])

    backend = get_backend()
    groups = [
        AreaResults(area=area, results=results)
        for area in get_areas()
        if (results := list(backend.search(area, terms)))
    ]

    return SearchResults(term=search_term, groups=groups)


def find_exact(term: str) -> models.Model | None:
    """Возвращает объект, поле которого точно совпадает с запросом, либо None.

    Проверяются области, для которых заданы поля точного совпадения
    (например, категории и персоны). Учитывается вариант запроса
    в переключённой раскладке клавиатуры.

    :param term: Строка поискового запроса.

    """
    search_term, terms = prepare_terms(term)

    if not search_term:
        return None

    for area in get_areas():

        if not area.exact_fields:
            continue

        query = Q()

        for field_name in area.exact_fields:

            for search_variant in terms:
                query |= Q(**{f'{field_name}__iexact': search_variant})

        if found := area.get_queryset().filter(query).first():
            return found

    return None
