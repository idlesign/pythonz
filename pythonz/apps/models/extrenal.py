from enum import unique, Enum
from itertools import chain

from django.db import models, IntegrityError
from etc.choices import ChoicesEnumMixin, get_choices

from .shared import UtmReady
from ..generics.models import RealmBaseModel
from ..integration.resources import PyDigestResource


class ExternalResource(UtmReady, RealmBaseModel):
    """Внешние ресурсы. Представляют из себя ссылки на страницы вне сайта."""

    @unique
    class Resource(ChoicesEnumMixin, Enum):

        PYDIGEST = 'pydigest', 'pythondigest.ru', PyDigestResource

    src_alias = models.CharField('Идентификатор источника', max_length=20, choices=get_choices(Resource))

    realm_name = models.CharField('Идентификатор области на pythonz', max_length=20)

    url = models.URLField('Страница ресурса', unique=True)

    title = models.CharField('Название', max_length=255)

    description = models.TextField('Описание', blank=True, default='')

    class Meta:

        verbose_name = 'Внешний ресурс'
        verbose_name_plural = 'Внешние ресурсы'
        ordering = ('-time_created',)

    @classmethod
    def fetch_new(cls):
        """Добывает данные из источников и складирует их."""

        for resource in list(cls.Resource):
            resource_alias = resource.title
            resource_cls = resource.hint

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
