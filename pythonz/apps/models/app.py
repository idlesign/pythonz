from typing import List
from random import choice
from time import sleep
from django.db import models
from django.db.models import QuerySet, Q
from etc.models import InheritedModel
from simple_history.models import HistoricalRecords
from sitecats.models import ModelWithCategory

from .discussion import ModelWithDiscussions
from .person import PersonsLinked
from ..generics.models import CommonEntityModel, ModelWithCompiledText, RealmBaseModel, ModelWithAuthorAndTranslator
from ..integration.pypistats import get_for_package


class App(
    InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
    ModelWithCompiledText, ModelWithAuthorAndTranslator, PersonsLinked):
    """Модель сущности `Приложение`."""

    COVER_UPLOAD_TO: str = 'apps'

    repo = models.URLField(
        'Репозиторий', null=True, blank=True, unique=True,
        help_text='URL, по которому доступен исходный код приложения.')

    authors = models.ManyToManyField('Person', verbose_name='Авторы', related_name='apps', blank=True)
    downloads = models.JSONField('Загрузки', default=dict)

    slug_pick: bool = True
    translator = None

    history = HistoricalRecords()

    persons_fields: List[str] = ['authors']

    class Meta:

        verbose_name = 'Приложение'
        verbose_name_plural = 'Приложения'

    class Fields:

        title = 'Название приложения'
        slug = 'Назание на PyPI'

        description = {
            'help_text': 'Краткое описание назначения приложения.',
        }

        text_src = {
            'verbose_name': 'Описание',
            'help_text': 'Более подробное описание назначения и функциональных особенностей приложения.',
        }

    @classmethod
    def find(cls, *search_terms: str) -> QuerySet:
        """Ищет указанный текст в приложениях. Возвращает QuerySet.

        :param search_terms: Строка для поиска.

        """
        q = Q()

        for term in search_terms:

            if not term:
                continue

            q |= Q(slug__icontains=term)

        return cls.objects.published().filter(q).order_by('time_published')

    @classmethod
    def actualize_downloads(cls, qs: QuerySet = None) -> int:
        """Актуализирует данные о загрузках приложений."""

        if qs is None:
            qs = cls.objects.published()

        apps = qs.filter(slug__isnull=False)

        updated = []

        for idx, app in enumerate(apps):

            if idx > 0:
                # У pypistats.org есть ограничени по кол-ву запросов с IP.
                # Пробуем быть особо вежливыми.
                sleep(choice((0.3, 0.8, 1.2)))

            if app.update_downloads():
                updated.append(app)

        if updated:
            cls.objects.bulk_update(updated, fields=['downloads'])

        return len(updated)

    @property
    def turbo_content(self) -> str:
        return self.make_html(self.description)

    @property
    def github_ident(self) -> str:
        repo = self.repo or ''

        prefix = 'https://github.com/'

        if not repo.startswith(prefix):
            return ''

        return repo.replace(prefix, '', 1)

    def on_publish(self):
        self.update_downloads()

    def update_downloads(self) -> bool:
        """Обновляет данные о загрузках пакета."""
        slug = self.slug

        if not slug:
            return False

        data = get_for_package(slug)

        downloads = self.downloads
        downloads.update(data)

        self.downloads = dict(sorted((
            item for item in downloads.items()), key=lambda item: item[0]))

        return bool(data)
