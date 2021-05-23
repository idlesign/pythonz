from enum import unique
from typing import List

from django.db import models
from etc.models import InheritedModel
from simple_history.models import HistoricalRecords
from sitecats.models import ModelWithCategory

from .discussion import ModelWithDiscussions
from .shared import UtmReady
from ..exceptions import RemoteSourceError
from ..generics.models import CommonEntityModel, ModelWithCompiledText, RealmBaseModel
from ..integration.utils import scrape_page


class Article(
    UtmReady, InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
    ModelWithCompiledText):
    """Модель сущности `Статья`."""

    allow_edit_anybody: bool = False
    paginator_defer: List[str] = ['url', 'text', 'text_src']

    @unique
    class Location(models.IntegerChoices):

        INTERNAL = 1, 'На этом сайте'
        # EXTERNAL = 2, 'На другом сайте'

    @unique
    class Source(models.IntegerChoices):

        HANDMADE = 1, 'Написана на этом сайте'
        SCRAPING = 2, 'Соскоблена с другого сайта'

    source = models.PositiveIntegerField(
        'Тип источника', choices=Source.choices, default=Source.HANDMADE,
        help_text='Указывает на механизм, при помощи которого статья появилась на сайте.')

    location = models.PositiveIntegerField(
        'Расположение статьи', choices=Location.choices, default=Location.INTERNAL,
        help_text='Статью можно написать прямо на этом сайте, либо сформировать статью-ссылку на внешний ресурс.')

    url = models.URLField(
        'URL статьи', null=True, blank=True, unique=True,
        help_text='Внешний URL, по которому доступна статья, которой вы желаете поделиться.')

    published_by_author = models.BooleanField('Я являюсь автором данной статьи', default=True)

    nofollow = models.BooleanField('Без перехода по ссылкам.', default=False)  # nofollow

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
    def turbo_content(self) -> str:
        return self.text

    @property
    def is_handmade(self) -> bool:
        """Возвращат флаг, указывающий на то, что статья создана на этом сайте."""
        return self.source == self.Source.HANDMADE

    def save(self, *args, **kwargs):

        # Для верного определения уникальности.
        if not self.url:
            self.url = None

        super().save(*args, **kwargs)

    def update_data_from_url(self, url: str):
        """Обновляет данные статьи, собирая информация, доступную по указанному URL.

        :param url:

        """
        result = scrape_page(url)

        if not result:
            raise RemoteSourceError('Не удалось получить данные статьи. Проверьте доступность указанного URL.')

        self.title = result['title']
        self.description = result['content_less']
        self.text_src = result['content_more']
        self.source = self.Source.SCRAPING
