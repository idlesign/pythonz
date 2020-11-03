from functools import partial
from typing import Dict, List, Tuple

from django.conf import settings
from django.db import models
from django.db.models import Q, QuerySet
from etc.models import InheritedModel

from .shared import UtmReady
from .user import User
from ..generics.models import ModelWithCompiledText, RealmBaseModel
from ..utils import PersonName, sync_many_to_many


class PersonsLinked(models.Model):
    """Примесь для моделей, имеющих поля многие-ко-многим, ссылающиеся на Person."""

    persons_fields: List[str] = []

    class Meta:

        abstract = True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_persons_fields()

    def sync_persons_fields(self, known_persons: Dict[str, List['Person']] = None):

        if not self.persons_fields:
            return

        if known_persons is None:
            known_persons = Person.get_known_persons()

        for field in self.persons_fields:
            src_field = field.rstrip('s')  # authors - > author
            self._sync_persons(getattr(self, src_field), field, known_persons)

    def _sync_persons(
        self,
        names_str: str,
        persons_field: str,
        known_persons: Dict[str, List['Person']],
        related_attr: str = 'name'
    ):
        names_list = []

        for name in names_str.split(','):
            # Убираем разметку типа [u:1:идле]
            name = name.strip(' []').rpartition(':')[2]
            name and names_list.append(name)

        sync_many_to_many(
            names_list, self, persons_field, related_attr, known_persons,
            unknown_handler=partial(self.create_person, publish=False))

    @classmethod
    def create_person(
        cls,
        person_name: str,
        known_persons: Dict[str, List['Person']],
        publish: bool = True
    ) -> 'Person':
        """Создаёт персону и добавляет её в словарь известных персон.

        :param person_name:
        :param known_persons:
        :param publish:

        """
        person = Person.create(person_name, save=True, publish=publish)
        Person.contribute_to_known_persons(person, known_persons)
        return person


class Person(UtmReady, InheritedModel, RealmBaseModel, ModelWithCompiledText):
    """Модель сущности `Персона`.

    Персона не обязана являться пользователем сайта, но между этими сущностями может быть связь.

    """
    details_related: List[str] = ['submitter', 'last_editor', 'user']
    paginator_related: List[str] = []
    paginator_order: str = 'name'
    items_per_page: int = 1000

    user = models.OneToOneField(
        User, verbose_name='Пользователь', related_name='person', null=True, blank=True,
        on_delete=models.SET_NULL)

    name = models.CharField('Имя', max_length=90, blank=True)

    name_en = models.CharField('Имя англ.', max_length=90, blank=True)

    aka = models.CharField('Другие имена', max_length=255, blank=True)  # Разделены ;

    class Meta:

        verbose_name = 'Персона'
        verbose_name_plural = 'Персоны'

    class Fields:

        text = {'verbose_name': 'Описание'}
        text_src = {'verbose_name': 'Описание (исх.)'}

    def __str__(self):
        return self.name

    @property
    def title(self) -> str:
        return self.get_display_name()

    @classmethod
    def get_known_persons(cls) -> Dict[str, List['Person']]:
        """Возвращает словарь, индексированный именами персон.

        Где значения являются списками с объектами моделей персон.
        Если в списке больше одной модели, значит этому имени соответствует
        несколько разных моделей персон.

        """
        known = {}

        for person in cls.objects.exclude(status=cls.Status.DELETED):
            cls.contribute_to_known_persons(person, known_persons=known)

        return known

    @classmethod
    def contribute_to_known_persons(cls, person: 'Person', known_persons: Dict[str, List['Person']]):
        """Добавляет объект указанной персоны в словарь с известными персонами.

        :param person:
        :param known_persons: Объект изменяется в ходе выполнения метода.

        """
        def add_name(name: str):
            """Заносит имя в разных вариантах в реестр известных имён.

            :param name:

            """
            name = PersonName(name)

            for variant in name.get_variants:

                persons_for_variant = known_persons.setdefault(variant, [])

                if person not in persons_for_variant:  # Дубли не нужны.
                    persons_for_variant.append(person)

        add_name(person.name)
        add_name(person.name_en)

        for aka_chunk in person.aka.split(';'):
            add_name(aka_chunk)

    @classmethod
    def find(cls, *search_terms: str) -> QuerySet:
        """Ищет персону по указанному имени. Возвращает QuerySet.

        :param search_terms: Строка для поиска.

        """
        q = Q()

        for term in search_terms:

            if not term:
                continue

            q |= Q(name__icontains=term) | Q(name_en__icontains=term) | Q(aka__icontains=term)

        return cls.get_actual().filter(q)

    @classmethod
    def create(cls, name: str, save: bool = False, publish: bool = True) -> 'Person':
        """Создаёт объект персоны по имени.

        :param name:
        :param save: Следует ли сохранить объект в БД.
        :param publish: Следует ли пометить объект опубликованным.

        """
        person = cls(
            name=name,
            name_en=name,
            status=cls.Status.PUBLISHED if publish else cls.Status.DRAFT,
            text_src='Описание отсутствует',
            submitter_id=settings.ROBOT_USER_ID,
        )

        if save:
            person.save(notify_published=False, notify_new=False)

        return person

    @classmethod
    def get_paginator_objects(cls) -> List:
        persons = super().get_paginator_objects()

        def sort_by_surname(person):
            split = person.name.rsplit(' ', 1)
            name = ' '.join(reversed(split))
            person.name = name
            return name

        result = sorted(persons, key=sort_by_surname)

        return result

    def get_materials(self) -> Dict[str, Tuple[str, QuerySet]]:
        """Возвращает словарь с матералами, созданными персоной.

        Индексирован названиями разделов сайта; значения — список моделей материалов.

        """
        from ..realms import get_realm

        realms = [
            get_realm('pep'),
            get_realm('book'),
            get_realm('video'),
            get_realm('app'),
        ]  # Пока ограничимся.

        materials = {}

        for realm in realms:

            realm_model = realm.model
            realm_name = realm_model.get_verbose_name_plural()

            _, plural = realm.get_names()

            items = getattr(self, plural)

            if realm.name != 'pep':
                items = items.published()

            items = items.order_by('slug', 'title')

            if items:
                materials[realm_name] = (plural, items)

        return materials
