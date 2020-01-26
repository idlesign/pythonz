from typing import List

from django.db import models
from etc.models import InheritedModel
from simple_history.models import HistoricalRecords
from sitecats.models import ModelWithCategory

from .discussion import ModelWithDiscussions
from .person import PersonsLinked
from .shared import HINT_IMPERSONAL_REQUIRED
from ..generics.models import CommonEntityModel, ModelWithAuthorAndTranslator, RealmBaseModel
from ..integration.videos import VideoBroker


class Video(
    InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
    ModelWithAuthorAndTranslator, PersonsLinked):
    """Модель сущности `Видео`."""

    COVER_UPLOAD_TO: str = 'videos'

    code = models.TextField('Код')

    url = models.URLField('URL')

    authors = models.ManyToManyField('Person', verbose_name='Авторы', related_name='videos', blank=True)

    history = HistoricalRecords()

    persons_fields: List[str] = ['authors']

    class Meta:

        verbose_name = 'Видео'
        verbose_name_plural = 'Видео'

    class Fields:

        title = 'Название видео'

        translator = 'Перевод/озвучание'

        description = {
            'help_text': f'Краткое описание того, о чём это видео. {HINT_IMPERSONAL_REQUIRED}',
        }

        linked = {
            'verbose_name': 'Связанные видео',
            'help_text': (
                'Выберите видео, которые имеют отношение к данному. '
                'Например, можно связать несколько эпизодов видео.'),
        }

        year = 'Год съёмок'

    @property
    def turbo_content(self) -> str:
        return self.make_html(self.description)

    @classmethod
    def get_supported_hostings(cls) -> List[str]:
        return list(VideoBroker.hostings.keys())

    def update_code_and_cover(self, url: str):

        embed_code, cover_url = VideoBroker.get_code_and_cover(url)

        self.code = embed_code
        self.update_cover_from_url(cover_url)
