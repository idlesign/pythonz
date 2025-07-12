from enum import unique
from itertools import chain

from django.db import IntegrityError, models

from ..generics.models import RealmBaseModel
from ..integration.resources import PyDigestResource
from .shared import UtmReady


class ExternalResource(UtmReady, RealmBaseModel):
    """Внешние ресурсы. Представляют из себя ссылки на страницы вне сайта."""

    @unique
    class Resource(models.TextChoices):

        PYDIGEST = 'pydigest', 'pythondigest.ru'

    RESOURCE_MAP = {
        Resource.PYDIGEST: PyDigestResource
    }

    src_alias = models.CharField('Идентификатор источника', max_length=20, choices=Resource.choices)

    realm_name = models.CharField('Идентификатор области на pythonz', max_length=20)

    url = models.URLField('Страница ресурса', unique=True)

    title = models.CharField('Название', max_length=255)

    description = models.TextField('Описание', blank=True, default='')

    is_external: bool = True
    """Признак внешнего ресурса.
    Используется в тех случаях, когда внешние ресурсы идут 
    вперемежку со внутренними.
    
    """

    class Meta:

        verbose_name = 'Внешний ресурс'
        verbose_name_plural = 'Внешние ресурсы'
        ordering = ('-time_created',)

    @classmethod
    def fetch_new(cls):
        """Добывает данные из источников и складирует их."""

        for resource_alias, resource_cls in cls.RESOURCE_MAP.items():
            resource_alias = resource_alias.value

            entries = resource_cls.fetch_entries()

            if not entries:
                return

            added = []
            existing = []

            for entry_data in entries:
                new_resource = cls(**entry_data)
                new_resource.src_alias = resource_alias
                new_resource.mark_published()

                try:
                    new_resource.save()
                    added.append(new_resource.url)

                except IntegrityError:
                    existing.append(new_resource.url)

            if added:
                # Оставляем только те записи, которые до сих пор выдаёт внешний ресурс.
                cls.objects.filter(src_alias=resource_alias).exclude(url__in=chain(added, existing)).delete()
