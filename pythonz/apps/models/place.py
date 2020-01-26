from typing import List, Tuple, Optional

from django.db import models, IntegrityError
from simple_history.models import HistoricalRecords

from .discussion import ModelWithDiscussions
from ..generics.models import RealmBaseModel
from ..integration.utils import get_location_data


class Place(RealmBaseModel, ModelWithDiscussions):
    """Географическое место. Для людей, событий и пр."""

    details_related: List[str] = ['last_editor']

    TYPE_COUNTRY = 'country'
    TYPE_LOCALITY = 'locality'
    TYPE_HOUSE = 'house'

    TYPES = (
        (TYPE_COUNTRY, 'Страна'),
        (TYPE_LOCALITY, 'Местность'),
        (TYPE_HOUSE, 'Здание'),
    )

    title = models.CharField('Название', max_length=255)

    description = models.TextField('Описание', blank=True, null=False, default='')

    geo_title = models.TextField('Полное название', null=True, blank=True, unique=True)

    geo_bounds = models.CharField('Пределы', max_length=255, null=True, blank=True)

    geo_pos = models.CharField('Координаты', max_length=255, null=True, blank=True)

    geo_type = models.CharField('Тип', max_length=25, null=True, blank=True, choices=TYPES, db_index=True)

    history = HistoricalRecords()

    class Meta:

        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def __str__(self):
        return self.geo_title

    @property
    def turbo_content(self) -> str:
        return self.make_html(self.description)

    def get_pos(self) -> Tuple[str, str]:
        """Возвращает координаты объекта в виде кортежа: (широта, долгота)."""
        lat, lng = self.geo_pos.split('|')
        return lat, lng

    def get_description(self) -> str:
        return self.description

    @classmethod
    def create_place_from_name(cls, name: str) -> Optional['Place']:
        """Создаёт место по его имени.

        :param name:

        """
        loc_data = get_location_data(name)

        if not loc_data:
            return None

        full_title = loc_data['name']

        place = cls(
            title=loc_data['requested_name'],
            geo_title=full_title,
            geo_bounds=loc_data['bounds'],
            geo_pos=loc_data['pos'],
            geo_type=loc_data['type']
        )

        try:
            place.save()

        except IntegrityError:
            place = cls.objects.get(geo_title=full_title)

        return place
