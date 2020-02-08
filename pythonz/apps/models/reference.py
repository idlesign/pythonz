from enum import unique
from typing import List

from django.db import models
from django.db.models import Q, QuerySet
from etc.models import InheritedModel
from simple_history.models import HistoricalRecords

from .discussion import ModelWithDiscussions
from .version import Version
from ..generics.models import CommonEntityModel, ModelWithCompiledText, RealmBaseModel


class ReferenceMissing(models.Model):
    """Промахи при поиске в справочнике."""

    term = models.CharField('Термин', max_length=255, unique=True)

    synonyms = models.TextField('Синонимы', blank=True)

    hits = models.PositiveIntegerField('Запросы', default=0)

    class Meta:

        verbose_name = 'Промах справочника'
        verbose_name_plural = 'Промахи справочника'

    def __str__(self):
        return self.term

    @classmethod
    def add(cls, search_term: str) -> bool:
        """Добавляет данные по указанному термину в реестр промахов.
        Возвращает True, если была добавлена новая запись.

        :param search_term: Термин для поиска.

        """
        obj = cls.objects.filter(
            Q(term__icontains=search_term) |
            Q(synonyms__icontains=search_term)

        ).first()

        if obj:
            obj.hits += 1
            obj.save()

        else:
            cls(term=search_term, hits=1).save()

        return obj is None


class Reference(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithDiscussions, ModelWithCompiledText):
    """Модель сущности `Справочник`."""

    autogenerate_slug: bool = True
    allow_linked: bool = False
    details_related: List[str] = ['parent', 'submitter']

    @unique
    class Type(models.IntegerChoices):

        CHAPTER = 1, 'Раздел справки'
        PACKAGE = 2, 'Описание пакета'
        MODULE = 3, 'Описание модуля'
        FUNCTION = 4, 'Описание функции'
        CLASS = 5, 'Описание класса/типа'
        METHOD = 6, 'Описание метода класса/типа'
        PROPERTY = 7, 'Описание свойства класса/типа'

    TYPES_CALLABLE = {
        Type.METHOD,
        Type.FUNCTION,
        Type.CLASS,
    }

    TYPES_BUNDLE = {
        Type.CHAPTER,
        Type.PACKAGE,
        Type.MODULE,
    }

    type = models.PositiveIntegerField(
        'Тип статьи', choices=Type.choices, default=Type.CHAPTER,
        help_text='Служит для структурирования информации. Справочные статьи разных типов могут выглядеть по-разному.')

    parent = models.ForeignKey(
        'self', related_name='children', verbose_name='Родитель', db_index=True, null=True, blank=True,
        help_text='Укажите родительский раздел. '
                  'Например, для модуля можно указать раздел справки, в которому он относится; '
                  'для метода &#8212; класс.',
        on_delete=models.CASCADE)

    version_added = models.ForeignKey(
        Version, related_name='%(class)s_added', verbose_name='Добавлено в', null=True, blank=True,
        help_text='Версия Python, для которой впервые стала актульна данная статья<br>'
                  '(версия, где впервые появился модуль, пакет, класс, функция).',
        on_delete = models.CASCADE)

    version_deprecated = models.ForeignKey(
        Version, related_name='%(class)s_deprecated', verbose_name='Устарело в', null=True, blank=True,
        help_text='Версия Python, для которой впервые данная статья перестала быть актуальной<br>'
        '(версия, где модуль, пакет, класс, функция были объявлены устаревшими).',
        on_delete=models.CASCADE)

    func_proto = models.CharField(
        'Прототип', max_length=250, null=True, blank=True,
        help_text='Для функций/методов. Описание интерфейса, например: <i>my_func(arg, kwarg=None)</i>')

    func_params = models.TextField(
        'Параметры', null=True, blank=True,
        help_text='Для функций/методов. Описание параметров функции.')

    func_result = models.CharField(
        'Результат', max_length=250, null=True, blank=True,
        help_text='Для функций/методов. Описание результата, например: <i>int</i>.')

    pep = models.PositiveIntegerField(
        'PEP', null=True, blank=True,
        help_text='Номер предложения по улучшению Питона, связанного с этой статьёй, например: <i>8</i> для PEP-8')

    search_terms = models.CharField(
        'Термины поиска', max_length=500, blank=True, default='',
        help_text='Дополнительные фразы, по которым можно найти данную статью, например: <i>«список», для «list»</i>')

    history = HistoricalRecords()

    class Meta:

        verbose_name = 'Статья справочника'
        verbose_name_plural = 'Справочник'
        ordering = ('parent_id', 'title')

    class Fields:

        title = {
            'verbose_name': 'Название',
            'help_text': ('Здесь следует указать название раздела справки '
                          'или пакета, модуля, класса, метода, функции и т.п.')
        }
        description = {
            'verbose_name': 'Кратко',
            'help_text': 'Краткое описание для раздела или пакета, модуля, класса, метода, функции и т.п.',
        }
        text_src = {
            'verbose_name': 'Описание',
            'help_text': 'Подробное описание. Здесь же следует располагать примеры кода.',
        }

    @property
    def turbo_content(self) -> str:
        return self.description

    @property
    def is_type_callable(self) -> bool:
        return self.type in self.TYPES_CALLABLE

    @property
    def is_type_bundle(self) -> bool:
        return self.type in self.TYPES_BUNDLE

    @property
    def is_type_method(self) -> bool:
        return self.type == self.Type.METHOD

    @property
    def is_type_module(self) -> bool:
        return self.type == self.Type.MODULE

    @property
    def is_type_class(self) -> bool:
        return self.type == self.Type.CLASS

    @property
    def is_type_chapter(self) -> bool:
        return self.type == self.Type.CHAPTER

    @classmethod
    def get_actual(cls, parent: 'Reference' = None, exclude_id: int = None) -> QuerySet:

        qs = cls.objects.published()

        if parent is not None:
            qs = qs.filter(parent=parent)

        if exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)

        return qs.order_by('-time_published').all()

    @classmethod
    def find(cls, *search_terms: str) -> QuerySet:
        """Ищет указанный текст в справочнике. Возвращает QuerySet.

        :param search_terms: Строка для поиска.

        """
        q = Q()

        for term in search_terms:

            if not term:
                continue

            q |= Q(title__icontains=term) | Q(search_terms__icontains=term)

        return cls.objects.published().filter(q).order_by('time_published')
