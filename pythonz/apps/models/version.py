from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from etc.models import InheritedModel

from .discussion import ModelWithDiscussions
from .shared import HINT_IMPERSONAL_REQUIRED
from ..generics.models import CommonEntityModel, ModelWithCompiledText, RealmBaseModel


class Version(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCompiledText):

    autogenerate_slug: bool = True
    items_per_page: int = 10

    current = models.BooleanField('Текущая', default=False)

    date = models.DateField('Дата выпуска')

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
