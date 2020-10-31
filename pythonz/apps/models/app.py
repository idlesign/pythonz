from typing import List

from django.db import models
from django.db.models import QuerySet, Q
from etc.models import InheritedModel
from simple_history.models import HistoricalRecords
from sitecats.models import ModelWithCategory

from .person import PersonsLinked
from .discussion import ModelWithDiscussions
from ..generics.models import CommonEntityModel, ModelWithCompiledText, RealmBaseModel, ModelWithAuthorAndTranslator


class App(
    InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
    ModelWithCompiledText, ModelWithAuthorAndTranslator, PersonsLinked):
    """Модель сущности `Приложение`."""

    COVER_UPLOAD_TO: str = 'apps'

    repo = models.URLField(
        'Репозиторий', null=True, blank=True, unique=True,
        help_text='URL, по которому доступен исходный код приложения.')

    authors = models.ManyToManyField('Person', verbose_name='Авторы', related_name='apps', blank=True)

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

    @property
    def turbo_content(self) -> str:
        return self.make_html(self.description)

    @property
    def github_ident(self) -> str:
        repo = self.repo

        prefix = 'https://github.com/'

        if not repo.startswith(prefix):
            return ''

        return repo.replace(prefix, '', 1)
