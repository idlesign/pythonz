from collections import namedtuple
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import QuerySet, FloatField
from django.db.models.functions import Cast
from django.utils import timezone
from etc.models import InheritedModel

from .discussion import ModelWithDiscussions
from .shared import HINT_IMPERSONAL_REQUIRED
from ..generics.models import CommonEntityModel, ModelWithCompiledText, RealmBaseModel

LifeTimeInfo = namedtuple('LifeTimeInfo', ['idx', 'since', 'till', 'pos1', 'pos2'])


class Version(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCompiledText):

    slug_pick: bool = True
    slug_auto: bool = True
    items_per_page: int = 10

    date = models.DateField('Дата выпуска')
    date_till = models.DateField('Окончание поддержки', null=True, blank=True)

    class Fields:

        title = {
            'verbose_name': 'Номер',
            'help_text': 'Номер версии с двумя обязательными разрядами и третим опциональным. Например: 2.7.12, 3.6.',
        }

        description = {
            'verbose_name': 'Введение',
            'help_text': 'Краткое описание основных изменений в версии.',
        }

        text_src = {
            'verbose_name': 'Описание',
            'help_text': (
                'Обзорное, более полное описание нововведений и изменений, произошедших в версии. '
                f'{HINT_IMPERSONAL_REQUIRED}'),
        }

    class Meta:

        verbose_name = 'Версия Python'
        verbose_name_plural = 'Версии Python'
        ordering = ('-date',)

    def __str__(self):
        return f'Python {self.title}'

    @property
    def current(self) -> bool:
        """Возвращает флаг, указывающий на то,
        является ли версия актуальной (поддерживается ли на текущий момент).

        """
        date = self.date
        date_till = self.date_till

        if not date or not date_till:
            return False

        now = timezone.now().date()

        return date < now < date_till

    @property
    def turbo_content(self) -> str:
        return self.text

    @classmethod
    def get_paginator_objects(cls) -> QuerySet:
        qs = super().get_paginator_objects()
        qs = qs.order_by('-date')
        return qs

    @classmethod
    def create_stub(cls, version_number: str) -> 'Version':
        """Создаёт запись о версии, основываясь только на номере.
        Использует для автоматического создания версий, например, из PEP.

        :param version_number:

        """
        stub = cls(
            title=version_number,
            description=f'Python версии {version_number}',
            text_src='Описание версии ещё не сформировано.',
            submitter_id=settings.ROBOT_USER_ID,
            date=timezone.now().date()
        )
        stub.save()

        return stub

    @classmethod
    def get_lifetime_data(cls):

        versions = cls.objects.exclude(
            date_till__isnull=True
        ).annotate(
            num=Cast('title', FloatField())
        ).order_by('num')

        def format_date(val):
            return val.strftime('%Y-%m-%d')

        now = timezone.now().date()
        delta = timedelta(days=1095)  # 3 года

        data = {
            'titles': [],
            'indexes': [],
            'info': [],
            'now': format_date(now),
            'range': f"'{format_date(now-delta)}', '{format_date(now+delta)}'"
        }

        next_pos = -0.1

        for idx, version in enumerate(versions):
            title = version.title
            data['titles'].append(title)
            data['indexes'].append(idx)
            data['info'].append(LifeTimeInfo(
                idx=idx,
                since=format_date(version.date),
                till=format_date(version.date_till),
                pos1=str(next_pos),
                pos2=str(next_pos + 0.2),
            ))
            next_pos += 1

        return data
