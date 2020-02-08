from datetime import timedelta, datetime
from enum import unique
from typing import Optional

from django.db import models
from django.db.models import F, QuerySet
from django.utils import timezone
from etc.models import InheritedModel
from simple_history.models import HistoricalRecords
from sitecats.models import ModelWithCategory

from .discussion import ModelWithDiscussions
from .place import Place
from .shared import UtmReady, HINT_IMPERSONAL_REQUIRED
from ..generics.models import CommonEntityModel, ModelWithCompiledText, ModelWithAuthorAndTranslator, RealmBaseModel


class Event(
    UtmReady, InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
    ModelWithCompiledText):
    """Модель сущности `Событие`."""

    @unique
    class Spec(models.IntegerChoices):

        DEDICATED = 1, 'Только Python'
        HAS_SECTION = 2, 'В основном Python'
        HAS_SOME = 3, 'Есть секция/отделение про Python'
        MOST = 4, 'Есть упоминания про Python'

    @unique
    class Type(models.IntegerChoices):

        MEETING = 1, 'Встреча'
        CONFERENCE = 2, 'Лекция'
        LECTURE = 3, 'Конференция'
        SPRINT = 4, 'Спринт'

    url = models.URLField('Страница в сети', null=True, blank=True)

    contacts = models.CharField(
        'Контактные лица', null=True, blank=True, max_length=255,
        help_text=(
            'Контактные лица через запятую, координирующие/устраивающие событие.'
            f'{ModelWithAuthorAndTranslator._hint_userlink}'))

    place = models.ForeignKey(
        Place, verbose_name='Место', related_name='events', null=True, blank=True,
        help_text=(
            'Укажите место проведения мероприятия.<br><b>Конкретный адрес следует указывать в описании.</b><br>'
            'Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».'),
        on_delete=models.CASCADE)

    specialization = models.PositiveIntegerField('Специализация', choices=Spec.choices, default=Spec.DEDICATED)

    type = models.PositiveIntegerField('Тип', choices=Type.choices, default=Type.MEETING)

    time_start = models.DateTimeField('Начало', null=True, blank=True)

    time_finish = models.DateTimeField(
        'Завершение', null=True, blank=True,
        help_text='Дату завершения можно и не указывать.')

    fee = models.BooleanField('Участие платное', default=False, db_index=True)

    history = HistoricalRecords()

    class Meta:

        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    class Fields:

        description = {
            'verbose_name': 'Краткое описание',
            'help_text': f'Краткое описание события. {HINT_IMPERSONAL_REQUIRED}',
        }

        text_src = {
            'verbose_name': 'Описание, контактная информация',
            'help_text': HINT_IMPERSONAL_REQUIRED,
        }

        cover = 'Логотип'

    def save(self, *args, **kwargs):

        if not self.pk:
            self.mark_published()

        super().save(*args, **kwargs)

    def get_display_type(self) -> str:
        return self.Type(self.type).label

    def get_display_specialization(self) -> str:
        return self.Spec(self.specialization).label

    @property
    def is_in_past(self) -> Optional[bool]:

        field = self.time_finish or self.time_start

        if field is None:
            return None

        return field < timezone.now()

    @property
    def is_now(self) -> bool:

        if not all([self.time_start, self.time_finish]):
            return False

        return self.time_start <= timezone.now() <= self.time_finish

    @property
    def time_forgetmenot(self) -> datetime:
        """Дата напоминания о предстоящем событии (на сутки ранее начала события)."""
        return self.time_start - timedelta(days=1)

    @classmethod
    def get_paginator_objects(cls) -> QuerySet:
        now = timezone.now()

        # Сначала грядущие в порядке приближения, потом прошедшие в порядке отдалённости.
        qs = cls.objects.published().annotate(
            past=models.Case(
                models.When(time_start__gte=now, then=False),
                models.When(time_start__lt=now, then=True),
                output_field=models.BooleanField(),
            )
        ).annotate(
            gap=models.Case(
                models.When(time_start__gte=now, then=F('time_start') - now),
                models.When(time_start__lt=now, then=now - F('time_start')),
                output_field=models.DurationField(),
            )
        ).order_by('past', 'gap')

        return qs
