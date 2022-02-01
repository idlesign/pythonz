from datetime import timedelta, datetime
from enum import unique
from typing import Optional, List

from django.db import models
from django.db.models import F, QuerySet
from django.utils import timezone
from django.utils.formats import date_format
from etc.models import InheritedModel
from simple_history.models import HistoricalRecords
from sitecats.models import ModelWithCategory

from .discussion import ModelWithDiscussions
from .place import WithPlace
from .shared import UtmReady, HINT_IMPERSONAL_REQUIRED
from ..generics.models import CommonEntityModel, ModelWithCompiledText, ModelWithAuthorAndTranslator
from ..integration.base import RemoteSource
from ..integration.events import EventSource


class Event(
    UtmReady, InheritedModel, CommonEntityModel, ModelWithDiscussions, ModelWithCategory,
    ModelWithCompiledText, WithPlace):
    """Модель сущности `Событие`."""

    allow_edit_published: bool = True
    notify_on_publish: bool = False
    paginator_defer: List[str] = ['contacts', 'text', 'text_src']
    utm_on_main: bool = False

    @unique
    class Spec(models.IntegerChoices):

        DEDICATED = 1, 'Только Python'
        HAS_SECTION = 2, 'В основном Python'
        HAS_SOME = 3, 'Есть секция/отделение про Python'
        MOST = 4, 'Есть упоминания про Python'

    @unique
    class Type(models.IntegerChoices):

        MEETING = 1, 'Встреча'
        CONFERENCE = 2, 'Конференция'
        LECTURE = 3, 'Лекция'
        SPRINT = 4, 'Спринт'

    source_group = EventSource

    contacts = models.CharField(
        'Контактные лица', null=True, blank=True, max_length=255,
        help_text=(
            'Контактные лица через запятую, координирующие/устраивающие событие.'
            f'{ModelWithAuthorAndTranslator._hint_userlink}'))

    specialization = models.PositiveIntegerField('Специализация', choices=Spec.choices, default=Spec.DEDICATED)

    type = models.PositiveIntegerField('Тип', choices=Type.choices, default=Type.MEETING)

    time_start = models.DateTimeField('Начало', null=True, blank=True)

    time_finish = models.DateTimeField(
        'Завершение', null=True, blank=True,
        help_text='Дату завершения можно и не указывать.')

    fee = models.BooleanField('Участие платное', null=True, blank=True, db_index=True)

    history = HistoricalRecords()

    class Meta:

        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        unique_together = ('src_alias', 'src_id')

    class Fields:

        description = {
            'verbose_name': 'Краткое описание',
            'help_text': f'Краткое описание события. {HINT_IMPERSONAL_REQUIRED}',
        }

        text_src = {
            'verbose_name': 'Описание, контактная информация',
            'help_text': HINT_IMPERSONAL_REQUIRED,
        }

        place = {
            'help_text': (
                'Укажите место проведения мероприятия.<br><b>Конкретный адрес следует указывать в описании.</b><br>'
                'Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».'),
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
    def page_title(self):

        title = f'{self.get_display_type()} {self.title}'
        time_start = self.time_start
        if time_start:
            title = f'{title} {date_format(time_start, "d E Y года")}'

        return title

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
    def get_featured(cls, *, candidate: 'Event', dt_stale: datetime) -> Optional['Event']:
        now = timezone.now()

        featured = cls.objects.published().filter(
            time_start__lte=now,
            time_finish__gt=now,
        ).first()

        if featured is None:
            return super().get_featured(candidate=candidate, dt_stale=dt_stale)

        return featured

    @classmethod
    def spawn_object(cls, item_data: dict, *, source: RemoteSource):

        big = item_data.pop('big')
        page_info = item_data.pop('__page_info')

        obj: Event = super().spawn_object(item_data, source=source)
        obj.specialization = cls.Spec.HAS_SECTION

        if big:
            obj.type = cls.Type.CONFERENCE

        if page_info:
            site_name = page_info.site_name
            description = page_info.description

            if description:
                if site_name == 'Meetup':
                    # Meetup в описание пихает мусорную конкатенацию.
                    description = page_info.title or ''

                obj.description = description

            images = page_info.images
            if images:
                image_src = images[0].get('src')
                if image_src:
                    obj.update_cover_from_url(image_src)

        return obj

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
