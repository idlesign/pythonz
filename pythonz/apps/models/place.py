from enum import unique
from typing import List, Tuple, Optional

from django.db import models, IntegrityError
from simple_history.models import HistoricalRecords

from .discussion import ModelWithDiscussions
from ..generics.models import RealmBaseModel, WithRemoteSource
from ..integration.base import RemoteSource
from ..integration.utils import get_location_data


class Place(RealmBaseModel, ModelWithDiscussions):
    """Географическое место. Для людей, событий и пр."""

    details_related: List[str] = ['last_editor']

    @unique
    class GeoType(models.TextChoices):

        COUNTRY = 'country', 'Страна'
        LOCALITY = 'locality', 'Местность'
        HOUSE = 'house', 'Здание'

    title = models.CharField('Название', max_length=255)

    description = models.TextField('Описание', blank=True, null=False, default='')

    geo_title = models.TextField('Полное название', null=True, blank=True, unique=True)

    geo_bounds = models.CharField('Пределы', max_length=255, null=True, blank=True)

    geo_pos = models.CharField('Координаты', max_length=255, null=True, blank=True)

    geo_type = models.CharField(
        'Тип', max_length=25, null=True, blank=True, choices=GeoType.choices, db_index=True)

    history = HistoricalRecords()

    class Meta:

        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def __str__(self):
        return self.geo_title or self.title

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


class WithPlace(WithRemoteSource):
    """Примесь для сущностей, которые могут связывать с местом."""

    src_place_name = models.CharField('Название места в источнике', max_length=255, default='')

    src_place_id = models.CharField('ID места в источнике', max_length=20, db_index=True, default='')

    place = models.ForeignKey(
        Place, verbose_name='Место', related_name='lnk_%(class)s', null=True, blank=True,
        on_delete=models.CASCADE)

    class Meta:

        abstract = True

    @classmethod
    def spawn_object(cls, item_data: dict, *, source: RemoteSource):
        obj = super().spawn_object(item_data, source=source)
        obj.link_to_place()
        return obj

    def link_to_place(self):
        """Связывает запись с местом Place, заполняя атрибут place_id."""

        # Попробуем найти ранее связанные записи.
        match = self.__class__.objects.filter(
            src_alias=self.src_alias,
            src_place_id=self.src_place_id,
        ).first()

        if match:
            self.place_id = match.place_id

        else:
            # Вычисляем место.
            match = Place.create_place_from_name(self.src_place_name)
            self.place_id = match.id
