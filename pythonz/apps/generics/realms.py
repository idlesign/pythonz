from django.conf.urls import url
from django.contrib.sitemaps import GenericSitemap
from django.urls import reverse
from sitetree.utils import item
from yaturbo import YandexTurboFeed

from .views import ListingView, DetailsView, AddView, EditView, TagsView
from ..utils import get_logger

LOGGER = get_logger('realms')
SYNDICATION_URL_MARKER = 'feed'
SYNDICATION_ITEMS_LIMIT = 15


class RealmBase:
    """Базовый класс области (книга, видео и пр)"""

    model = None
    """Класс модели, связанный с областью"""

    form = None
    """Форма, связанная с областью."""

    icon = 'icon'
    """Иконка, символизирующая область."""

    name = None
    """Имя области. Ед.ч."""
    name_plural = None
    """Имя области. Мн. ч."""

    allowed_views = ('listing', 'details', 'tags', 'add', 'edit')
    """Имена доступных представлений."""

    show_on_main = True
    """Следует ли отображать на главной странице."""
    show_on_top = True
    """Следует ли отображать в верхнем меню."""

    sitetree_items = None
    """Кеш элементов древа сайта для данной области."""

    ready_for_digest = True
    """Указывает на готовность области попасть в еженедельный сводки."""

    syndication_enabled = True
    """Указание на то, доступна ли синдикация."""
    syndication_url = None
    """URL синдикации."""
    syndication_feed = None
    """Кеш синдикации."""

    sitemap_enabled = True
    """Указание на то, включена ли для области карта сайта."""
    sitemap = None
    """Кеш карты сайта для данной области."""
    sitemap_date_field = 'time_modified'
    """Поле даты в моделях области (для карты сайта)."""
    sitemap_changefreq = 'daily'
    """Предполагаемая периодичность обновления данных (для карты сайта)."""

    txt_form_add = 'Добавить элемент'
    txt_form_edit = 'Редактировать элемент'

    # Представление списка.
    view_listing = None
    view_listing_base_class = ListingView
    view_listing_url = r'^$'
    view_listing_title = None
    view_listing_description = ''
    view_listing_keywords = ''

    # Представление с детальной информацией.
    view_details = None
    view_details_base_class = DetailsView
    view_details_url = r'^(?P<obj_id>\d+)/$'
    view_details_slug_url = r'^named/(?P<obj_id>[0-9A-z\.-]+)/$'

    # Представление для добавления нового элемента.
    view_add = None
    view_add_base_class = AddView
    view_add_url = r'^add/$'

    # Представление для редактирования.
    view_edit = None
    view_edit_base_class = EditView
    view_edit_url = r'^edit/(?P<obj_id>\d+)/$'

    # Представление с разбивкой элементов по категориям.
    view_tags = None
    view_tags_base_class = TagsView
    view_tags_url = r'^tags/(?P<category_id>\d+)/$'

    @classmethod
    def init(cls):
        """Инициализатор обсласти. Наследники могут использовать для своих нужд."""

    @classmethod
    def is_allowed_edit(cls):
        """Возвращает флаг, указывающий на возможность редактирования объектов
        в данной области.

        :return:
        """
        return 'edit' in cls.allowed_views

    @classmethod
    def _get_syndication_feed(cls, title, description, func_link, func_items, cls_name):
        from ..integration.utils import get_thumb_url

        type_dict = {
            'title': title,
            'description': f'PYTHONZ. {description}',
            'item_enclosure_mime_type': 'image/png',
            'item_enclosure_length': 50000,
            'item_enclosure_url': lambda self, item: (
                get_thumb_url(item.realm, item.cover, 100, 131, absolute_url=True) if hasattr(item, 'cover') else ''),
            'link': func_link,
            'items': func_items,
            'item_title': lambda self, item: item.title,
            'item_pubdate': lambda self, item: item.time_published,
            'item_link': lambda self, item: item.get_absolute_url(),
            'item_guid': lambda self, item: f'{cls.name}_{item.pk}',
            'item_description': lambda self, item: item.description,
            'item_turbo': lambda self, item: item.turbo_content,
        }

        feed_cls = type(f'{cls_name}Syndication', (YandexTurboFeed,), type_dict)()  # type: YandexTurboFeed
        feed_cls.turbo_sanitize = True

        return feed_cls

    @classmethod
    def get_syndication_feed(cls):
        """Возвращает объект потока синдикации (RSS).

        :return:
        """
        def get_items(self):
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
    def get_sitemap(cls):
        """Возвращает объект карты сайта (sitemap).

        :return:
        """
        if cls.sitemap is None:
            settings = {
                'queryset': cls.model.get_actual(),
                'date_field': cls.sitemap_date_field,
            }
            cls.sitemap = GenericSitemap(settings, priority=0.5, changefreq=cls.sitemap_changefreq)
        return cls.sitemap

    @classmethod
    def get_listing_urlname(cls):
        """Возвращает название URL страницы со списком объектов.

        :return:
        """
        _tmp, realm_name_plural = cls.get_names()
        return f'{realm_name_plural}:listing'

    @classmethod
    def get_details_urlname(cls, slugged=False):
        """Возвращает название URL страницы с детальной информацией об объекте.

        :param bool slugged Следует ли вернуть название для URL человекопонятного
            (см. CommonEntityModel.autogenerate_slug).
        :rtype: str

        """
        _tmp, realm_name_plural = cls.get_names()
        name = f'{realm_name_plural}:details'
        if slugged:
            name += '_slug'
        return name

    @classmethod
    def get_sitetree_details_item(cls):
        """Возвращает элемент древа сайта, указывающий на страницу с детальной информацией об объекте.

        :return:
        """
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
        if getattr(cls.model, 'autogenerate_slug', False):
            items.append(get_item(cls.get_details_urlname(slugged=True), id_attr='slug'))

        return items

    @classmethod
    def get_edit_urlname(cls):
        """Возвращает название URL страницы редактирования объекта.

        :return:
        """
        _tmp, realm_name_plural = cls.get_names()
        return f'{realm_name_plural}:edit'

    @classmethod
    def get_sitetree_edit_item(cls):
        """Возвращает элемент древа сайта, указывающий на страницу редактирования объекта.

        :return:
        """
        realm_name, _tmp = cls.get_names()
        return item(cls.txt_form_edit, f'{cls.get_edit_urlname()} {realm_name}.id',
                    in_menu=False, in_sitetree=False, access_loggedin=True)

    @classmethod
    def get_add_urlname(cls):
        """Возвращает название URL страницы добавления объекта.

        :return:
        """
        _tmp, realm_name_plural = cls.get_names()
        return f'{realm_name_plural}:add'

    @classmethod
    def get_sitetree_add_item(cls):
        """Возвращает элемент древа сайта, указывающий на страницу добавления объекта.

        :return:
        """

        tree_item = item(cls.txt_form_add, cls.get_add_urlname(), access_loggedin=True)
        tree_item.show_on_top = True

        return tree_item

    @classmethod
    def get_tags_urlname(cls):
        """Возвращает название URL страницы со списком объектов в определённой категории.

        :return:
        """
        _tmp, realm_name_plural = cls.get_names()
        return f'{realm_name_plural}:tags'

    @classmethod
    def get_sitetree_tags_item(cls):
        """Возвращает элемент древа сайта, указывающий на страницу разбивки объектов по метке (категории).

        :return:
        """
        return item('Категория «{{ category.title }}»', f'{cls.get_tags_urlname()} category.id',
                    in_menu=False, in_sitetree=False)

    @classmethod
    def get_sitetree_items(cls):
        """Возвращает элементы древа сайта.

        :return:
        """
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
    def get_names(cls):
        """Возвращает кортеж с именами области в ед. и мн. числах.

        :return:
        """
        if cls.name is None:
            cls.name = cls.__name__.lower().replace('realm', '')

        if cls.name_plural is None:
            cls.name_plural = f'{cls.name}s'

        return cls.name, cls.name_plural

    @classmethod
    def get_view(cls, name):
        """Формирует и возвращает объект представления.

        :param name:
        :return:
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
    def get_syndication_url(cls):
        """Возвращает URL потока синдикации (RSS).

        :return:
        """
        if cls.syndication_url is None:
            cls.syndication_url = reverse(f'{cls.name_plural}:syndication')
        return cls.syndication_url

    @classmethod
    def get_urls(cls):
        """Вовзвращает набор URL, актуальных для этой области.

        :return:
        """
        views = []

        def add_view(view_name, url_name=None):

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
