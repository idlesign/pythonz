from typing import Callable, List, Tuple, Type

from django.conf.urls import url
from django.contrib.sitemaps import GenericSitemap
from django.db.models import QuerySet
from django.urls import reverse
from sitetree.models import TreeItemBase
from sitetree.utils import item
from yaturbo import YandexTurboFeed

from .forms import CommonEntityForm
from .views import ListingView, DetailsView, AddView, EditView, TagsView, RealmView
from ..integration.utils import get_thumb_url
from ..utils import get_logger

if False:  # pragma: nocover
    from .models import RealmBaseModel


LOGGER = get_logger('realms')
SYNDICATION_URL_MARKER = 'feed'
SYNDICATION_ITEMS_LIMIT = 15


class RealmBase:
    """Базовый класс области (книга, видео и пр)"""

    model: Type['RealmBaseModel'] = None
    """Класс модели, связанный с областью"""

    form: Type[CommonEntityForm] = None
    """Форма, связанная с областью."""

    icon: str = 'icon'
    """Иконка, символизирующая область."""

    name: str = None
    """Имя области. Ед.ч."""
    name_plural: str = None
    """Имя области. Мн. ч."""

    allowed_views: Tuple[str, ...] = ('listing', 'details', 'tags', 'add', 'edit')
    """Имена доступных представлений."""

    show_on_main: bool = True
    """Следует ли отображать на главной странице."""
    show_on_top: bool = True
    """Следует ли отображать в верхнем меню."""

    sitetree_items: TreeItemBase = None
    """Кеш элементов древа сайта для данной области."""

    ready_for_digest: bool = True
    """Указывает на готовность области попасть в еженедельный сводки."""

    syndication_enabled: bool = True
    """Указание на то, доступна ли синдикация."""
    syndication_url: str = None
    """URL синдикации."""
    syndication_feed: YandexTurboFeed = None
    """Кеш синдикации."""

    sitemap_enabled: bool = True
    """Указание на то, включена ли для области карта сайта."""
    sitemap: GenericSitemap = None
    """Кеш карты сайта для данной области."""
    sitemap_date_field: str = 'time_modified'
    """Поле даты в моделях области (для карты сайта)."""
    sitemap_changefreq: str = 'daily'
    """Предполагаемая периодичность обновления данных (для карты сайта)."""

    txt_form_add: str = 'Добавить элемент'
    txt_form_edit: str = 'Редактировать элемент'

    # Представление списка.
    view_listing = None
    view_listing_base_class: Type[RealmView] = ListingView
    view_listing_url: str = r'^$'
    view_listing_title: str = None
    view_listing_description: str = ''
    view_listing_keywords: str = ''

    # Представление с детальной информацией.
    view_details = None
    view_details_base_class: Type[RealmView] = DetailsView
    view_details_url: str = r'^(?P<obj_id>\d+)/$'
    view_details_slug_url: str = r'^named/(?P<obj_id>[0-9A-z\.-]+)/$'

    # Представление для добавления нового элемента.
    view_add = None
    view_add_base_class: Type[RealmView] = AddView
    view_add_url: str = r'^add/$'

    # Представление для редактирования.
    view_edit = None
    view_edit_base_class: Type[RealmView] = EditView
    view_edit_url: str = r'^edit/(?P<obj_id>\d+)/$'

    # Представление с разбивкой элементов по категориям.
    view_tags = None
    view_tags_base_class: Type[RealmView] = TagsView
    view_tags_url: str = r'^tags/(?P<category_id>\d+)/$'

    @classmethod
    def init(cls):
        """Инициализатор обсласти. Наследники могут использовать для своих нужд."""

    @classmethod
    def is_allowed_edit(cls) -> bool:
        """Возвращает флаг, указывающий на возможность редактирования объектов
        в данной области.

        """
        return 'edit' in cls.allowed_views

    @classmethod
    def _get_syndication_feed(
        cls,
        title: str,
        description: str,
        func_link: Callable,
        func_items: Callable,
        cls_name: str
    ) -> YandexTurboFeed:

        type_dict = {
            'title': title,
            'description': f'PYTHONZ. {description}',
            'item_enclosure_mime_type': 'image/png',
            'item_enclosure_length': 50000,
            'item_enclosure_url': lambda self, item: (
                get_thumb_url(item.realm, item.cover, 100, 131, absolute_url=True)
                if hasattr(item, 'cover') else ''
            ),
            'link': func_link,
            'items': func_items,
            'item_title': lambda self, item: item.title,
            'item_pubdate': lambda self, item: item.time_published,
            'item_link': lambda self, item: item.get_absolute_url(),
            'item_guid': lambda self, item: f'{cls.name}_{item.pk}',
            'item_description': lambda self, item: item.description,
            'item_turbo': lambda self, item: item.turbo_content,
        }

        feed_cls: YandexTurboFeed = type(f'{cls_name}Syndication', (YandexTurboFeed,), type_dict)()
        feed_cls.turbo_sanitize = True

        return feed_cls

    @classmethod
    def get_syndication_feed(cls) -> YandexTurboFeed:
        """Возвращает объект потока синдикации (RSS)."""

        def get_items(self) -> QuerySet:
            items = []

            try:
                items = cls.model.get_actual()[:SYNDICATION_ITEMS_LIMIT]

            except AttributeError:
                # todo Затычка для модели Categories. Убрать фиктивный RSS при случае.
                pass

            return items

        if cls.syndication_feed is None:

            title = cls.model._meta.verbose_name_plural

            cls.syndication_feed = cls._get_syndication_feed(
                title=title,
                description=f'Материалы в разделе «{title}»',
                func_link=lambda self: reverse(cls.get_listing_urlname()),
                func_items=get_items,
                cls_name=cls.name
            )

        return cls.syndication_feed

    @classmethod
    def get_sitemap(cls) -> GenericSitemap:
        """Возвращает объект карты сайта (sitemap)."""

        if cls.sitemap is None:
            settings = {
                'queryset': cls.model.get_actual(),
                'date_field': cls.sitemap_date_field,
            }
            cls.sitemap = GenericSitemap(settings, priority=0.5, changefreq=cls.sitemap_changefreq)

        return cls.sitemap

    @classmethod
    def get_listing_urlname(cls) -> str:
        """Возвращает название URL страницы со списком объектов."""
        _tmp, realm_name_plural = cls.get_names()

        return f'{realm_name_plural}:listing'

    @classmethod
    def get_details_urlname(cls, slugged: bool = False) -> str:
        """Возвращает название URL страницы с детальной информацией об объекте.

        :param slugged Следует ли вернуть название для URL человекопонятного
            (см. CommonEntityModel.slug_auto).

        """
        _tmp, realm_name_plural = cls.get_names()

        name = f'{realm_name_plural}:details'

        if slugged:
            name += '_slug'

        return name

    @classmethod
    def get_sitetree_details_item(cls) -> List[TreeItemBase]:
        """Возвращает элемент древа сайта, указывающий на страницу с детальной информацией об объекте."""

        realm_name, realm_name_plural = cls.get_names()

        children = []

        if 'edit' in cls.allowed_views:
            children.append(cls.get_sitetree_edit_item())

        details_urlname = cls.get_details_urlname()

        def get_item(urlname, id_attr='id'):
            return item(
                '{{ %s }}' % realm_name,
                f'{urlname} {realm_name}.{id_attr}',  # Например books:details book.id
                children=children,
                in_menu=False,
                in_sitetree=False
            )

        items = [get_item(details_urlname)]

        if getattr(cls.model, 'slug_pick', False):
            items.append(get_item(cls.get_details_urlname(slugged=True), id_attr='slug'))

        return items

    @classmethod
    def get_edit_urlname(cls) -> str:
        """Возвращает название URL страницы редактирования объекта."""
        _tmp, realm_name_plural = cls.get_names()

        return f'{realm_name_plural}:edit'

    @classmethod
    def get_sitetree_edit_item(cls) -> TreeItemBase:
        """Возвращает элемент древа сайта, указывающий на страницу редактирования объекта."""
        realm_name, _tmp = cls.get_names()

        return item(
            cls.txt_form_edit, f'{cls.get_edit_urlname()} {realm_name}.id',
            in_menu=False, in_sitetree=False, access_loggedin=True)

    @classmethod
    def get_add_urlname(cls) -> str:
        """Возвращает название URL страницы добавления объекта."""
        _tmp, realm_name_plural = cls.get_names()

        return f'{realm_name_plural}:add'

    @classmethod
    def get_sitetree_add_item(cls) -> TreeItemBase:
        """Возвращает элемент древа сайта, указывающий на страницу добавления объекта."""

        tree_item = item(cls.txt_form_add, cls.get_add_urlname(), access_loggedin=True)
        tree_item.show_on_top = True

        return tree_item

    @classmethod
    def get_tags_urlname(cls) -> str:
        """Возвращает название URL страницы со списком объектов в определённой категории."""
        _tmp, realm_name_plural = cls.get_names()

        return f'{realm_name_plural}:tags'

    @classmethod
    def get_sitetree_tags_item(cls) -> TreeItemBase:
        """Возвращает элемент древа сайта, указывающий на страницу разбивки объектов по метке (категории)."""
        return item(
            'Категория «{{ category.title }}»', f'{cls.get_tags_urlname()} category.id',
            in_menu=False, in_sitetree=False)

    @classmethod
    def get_sitetree_items(cls) -> TreeItemBase:
        """Возвращает элементы древа сайта."""

        if cls.sitetree_items is None:
            children = []

            for view_name in cls.allowed_views:

                if view_name not in ('listing', 'edit'):
                    items = getattr(cls, f'get_sitetree_{view_name}_item')()

                    if not isinstance(items, list):
                        items = [items]

                    children.extend(items)

            cls.sitetree_items = item(
                cls.view_listing_title or str(cls.model._meta.verbose_name_plural),
                cls.get_listing_urlname(),
                description=cls.view_listing_description,
                children=children,
            )

            cls.sitetree_items.show_on_top = cls.show_on_top

        return cls.sitetree_items

    @classmethod
    def get_names(cls) -> Tuple[str, str]:
        """Возвращает кортеж с именами области в ед. и мн. числах."""

        if cls.name is None:
            cls.name = cls.__name__.lower().replace('realm', '')

        if cls.name_plural is None:
            cls.name_plural = f'{cls.name}s'

        return cls.name, cls.name_plural

    @classmethod
    def get_view(cls, name: str) -> RealmView:
        """Формирует и возвращает объект представления.

        :param name:

        """
        view_attr_name = f'view_{name}'
        view = getattr(cls, view_attr_name)

        if view is None:
            realm_name, _ = cls.get_names()
            base_view_class = getattr(cls, f'view_{name}_base_class')

            class_dict = {
                'realm': cls,
                'name': name
            }

            view = type(f'{realm_name.capitalize()}{name.capitalize()}View', (base_view_class,), class_dict)
            setattr(cls, view_attr_name, view)

        return view

    @classmethod
    def get_syndication_url(cls) -> str:
        """Возвращает URL потока синдикации (RSS)."""

        if cls.syndication_url is None:
            cls.syndication_url = reverse(f'{cls.name_plural}:syndication')

        return cls.syndication_url

    @classmethod
    def get_urls(cls) -> List:
        """Вовзвращает набор URL, актуальных для этой области."""
        views = []

        def add_view(view_name: str, url_name: str = None):

            if url_name is None:
                url_name = view_name

            views.append(
                url(getattr(cls, f'view_{url_name}_url'), cls.get_view(view_name).as_view(), name=url_name)
            )

        for view_name in cls.allowed_views:
            add_view(view_name)

            if view_name == 'details':
                add_view(view_name, 'details_slug')

        if cls.syndication_enabled:
            views.append(url(fr'^{SYNDICATION_URL_MARKER}/$', cls.get_syndication_feed(), name='syndication'))

        _, realm_name_plural = cls.get_names()

        return [url(fr'^{realm_name_plural}/', (views, realm_name_plural, realm_name_plural))]
