
from django.db import models
from etc.models import InheritedModel
from simple_history.models import HistoricalRecords
from sitecats.models import ModelWithCategory

from ..generics.models import CommonEntityModel, ModelWithAuthorAndTranslator, RealmBaseModel
from .discussion import ModelWithDiscussions
from .partner import ModelWithPartnerLinks
from .person import PersonsLinked
from .shared import HINT_IMPERSONAL_REQUIRED


class Book(
    InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
    ModelWithAuthorAndTranslator, ModelWithPartnerLinks, PersonsLinked):
    """Модель сущности `Книга`."""

    COVER_UPLOAD_TO: str = 'books'

    isbn = models.CharField('ISBN', max_length=20, unique=True, null=True, blank=True)

    isbn_ebook = models.CharField('ISBN эл. книги', max_length=20, unique=True, null=True, blank=True)

    authors = models.ManyToManyField('Person', verbose_name='Авторы', related_name='books', blank=True)

    history = HistoricalRecords()

    persons_fields: list[str] = ['authors']

    class Meta:

        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'

    class Fields:

        title = 'Название книги'

        description = {
            'verbose_name': 'Аннотация',
            'help_text': f'Аннотация к книге, или другое краткое описание. {HINT_IMPERSONAL_REQUIRED}',
        }

        linked = {
            'verbose_name': 'Связанные книги',
            'help_text': (
                'Выберите книги, которые имеют отношение к данной. '
                'Например, для книги-перевода можно указать оригинал.',)
        }

        year = 'Год издания'

    @property
    def turbo_content(self) -> str:
        return self.make_html(self.description)
