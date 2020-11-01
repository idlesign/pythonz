from typing import List

from django.db import models
from etc.models import InheritedModel
from simple_history.models import HistoricalRecords
from sitecats.models import ModelWithCategory

from .discussion import ModelWithDiscussions
from .place import Place
from .shared import UtmReady, HINT_IMPERSONAL_REQUIRED
from ..generics.models import CommonEntityModel, ModelWithCompiledText, ModelWithAuthorAndTranslator, RealmBaseModel


class Community(
    UtmReady, InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
    ModelWithCompiledText):
    """Модель сообществ. Формально объединяет некоторую группу людей."""

    allow_edit_published: bool = True
    paginator_defer: List[str] = ['url', 'text', 'text_src']

    place = models.ForeignKey(
        Place, verbose_name='Место', related_name='communities', null=True, blank=True,
        help_text='Для географически локализованных сообществ можно указать место (страна, город, село).<br>'
                  'Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».',
        on_delete=models.SET_NULL)

    contacts = models.CharField(
        'Контактные лица', null=True, blank=True, max_length=255,
        help_text=(
            'Контактные лица через запятую, представляющие сообщество, координаторы, основатели.'
            f'{ModelWithAuthorAndTranslator._hint_userlink}'))

    url = models.URLField('Страница в сети', null=True, blank=True)

    history = HistoricalRecords()

    class Meta:

        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'

    class Fields:

        title = 'Название сообщества'

        cover = 'Логотип'

        description = {
            'verbose_name': 'Кратко',
            'help_text': (
                'Сжатая предварительная информация о сообществе (например, направление деятельности). '
                f'{HINT_IMPERSONAL_REQUIRED}')
        }

        text_src = {
            'verbose_name': 'Описание, принципы работы, правила, контактная информация',
            'help_text': HINT_IMPERSONAL_REQUIRED,
        }

        linked = {
            'verbose_name': 'Связанные сообщества',
            'help_text': 'Выберите сообщества, имеющие отношение к данному.',
        }

        year = 'Год образования'

    @property
    def turbo_content(self) -> str:
        return self.text

    def save(self, *args, **kwargs):

        if not self.pk:
            self.mark_published()

        super().save(*args, **kwargs)
