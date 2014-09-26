from sitetree.utils import item
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.contrib.sitemaps import GenericSitemap
from django.contrib.syndication.views import Feed

from .views import ListingView, DetailsView, AddView, EditView, TagsView


class RealmBase(object):
    """Базовый класс области (книга, видео и пр)"""

    model = None  # Класс модели, связанный с областью
    form = None  # Форма, связанная с областью.
    icon = 'icon'  # Иконка, символизирующая область.

    # Название области.
    name = None  # Имя области. Ед.ч.
    name_plural = None  # Имя области. Мн. ч.

    # Имена доступных представлений.
    allowed_views = ('listing', 'details', 'tags', 'add', 'edit')

    # Кеш элементов древа сайта для данной области.
    sitetree_items = None

    # Указывает на готовность области попасть в еженедельный дайджест.
    ready_for_digest = True

    # Указание на то, доступна ли синдикация.
    syndication_enabled = True

    # URL синдикации.
    syndication_url = None

    # Кеш синдикации.
    syndication_feed = None

    # Указание на то, включена ли для области карта сайта.
    sitemap_enabled = True

    # Кеш карты сайта для данной области.
    sitemap = None

    # Поле даты в моделях области (для карты сайта).
    sitemap_date_field = 'time_modified'

    # Предполагаемая периодичность обновления данных (для карты сайта).
    sitemap_changefreq = 'weekly'

    txt_promo = 'Если вы это читаете, значит здесь требуется нормальное описание.'
    txt_form_add = 'Добавить элемент'
    txt_form_edit = 'Редактировать элемент'

    # Представление списка.
    view_listing = None
    view_listing_base_class = ListingView
    view_listing_url = r'^$'

    # Представление с детальной информацией.
    view_details = None
    view_details_base_class = DetailsView
    view_details_url = r'^(?P<obj_id>\d+)/$'

    # Представление для добавления нового элемента.
    view_add = None
    view_add_base_class = AddView
    view_add_url = r'^add/$'

    # Представление для редактирования.
    view_edit = None
    view_edit_base_class = EditView
    view_edit_url = r'^(?P<obj_id>\d+)/edit/$'

    # Представление с разбивкой элементов по категориям.
    view_tags = None
    view_tags_base_class = TagsView
    view_tags_url = r'^tags/(?P<category_id>\d+)/$'

    @classmethod
    def is_allowed_edit(cls):
        """Возвращает флаг, указывающий на возможность редактирования объектов
        в данной области.

        :return:
        """
        return 'edit' in cls.allowed_views

    @classmethod
    def get_syndication_feed(cls):
        """Возвращает объект потока синдикации (RSS).

        :return:
        """
        if cls.syndication_feed is None:
            name = cls.model._meta.verbose_name_plural
            type_dict = {
                'title': name,
                'description': 'PYTHONZ. Новое в разделе «%s»' % name,
                'link': lambda self: reverse(cls.get_listing_urlname()),
                'items': lambda self: cls.model.get_actual(),
                'item_title': lambda self, item: item.title,
                'item_link': lambda self, item: item.get_absolute_url(),
                'item_description': lambda self, item: item.description,
            }
            cls.syndication_feed = type('%sSyndication' % cls.name, (Feed,), type_dict)()
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
        return '%s:listing' % realm_name_plural

    @classmethod
    def get_sitetree_listing_item(cls):
        """Возвращает элемент древа сайта, указывающий на страницу со списком объектов.

        :return:
        """
        return item('Список', cls.get_listing_urlname(), in_menu=False)

    @classmethod
    def get_details_urlname(cls):
        """Возвращает название URL страницы с детальной информацией об объекте.

        :return:
        """
        _tmp, realm_name_plural = cls.get_names()
        return '%s:details' % realm_name_plural

    @classmethod
    def get_sitetree_details_item(cls):
        """Возвращает элемент древа сайта, указывающий на страницу с детальной информацией об объекте.

        :return:
        """
        realm_name, realm_name_plural = cls.get_names()
        children = []
        if 'edit' in cls.allowed_views:
            children.append(cls.get_sitetree_edit_item())
        return item('{{ %s.title }}' % realm_name, '%s %s.id' % (cls.get_details_urlname(), realm_name), children=children, in_menu=False, in_sitetree=False)

    @classmethod
    def get_sitetree_edit_item(cls):
        """Возвращает элемент древа сайта, указывающий на страницу редактирования объекта.

        :return:
        """
        realm_name, realm_name_plural = cls.get_names()
        return item(cls.txt_form_edit, '%s:edit %s.id' % (realm_name_plural, realm_name), in_menu=False, in_sitetree=False, access_loggedin=True)

    @classmethod
    def get_sitetree_add_item(cls):
        """Возвращает элемент древа сайта, указывающий на страницу добавления объекта.

        :return:
        """
        realm_name, realm_name_plural = cls.get_names()
        return item(cls.txt_form_add, '%s:add' % realm_name_plural, access_loggedin=True)

    @classmethod
    def get_tags_urlname(cls):
        """Возвращает название URL страницы со списком объектов в определённой категории.

        :return:
        """
        _tmp, realm_name_plural = cls.get_names()
        return '%s:tags' % realm_name_plural

    @classmethod
    def get_sitetree_tags_item(cls):
        """Возвращает элемент древа сайта, указывающий на страницу разбивки объектов по метке (категории).

        :return:
        """
        return item('Категория «{{ category.title }}»', '%s category.id' % cls.get_tags_urlname(), in_menu=False, in_sitetree=False)

    @classmethod
    def get_sitetree_items(cls):
        """Возвращает элементы древа сайта.

        :return:
        """
        if cls.sitetree_items is None:
            cls.sitetree_items = item(
                str(cls.model._meta.verbose_name_plural), cls.get_listing_urlname(),
                children=[getattr(cls, 'get_sitetree_%s_item' % view_name)() for view_name in cls.allowed_views if view_name != 'edit']
            )
        return cls.sitetree_items

    @classmethod
    def get_names(cls):
        """Возвращает кортеж с именами области в ед. и мн. числах.

        :return:
        """
        if cls.name is None:
            cls.name = cls.__name__.lower().replace('realm', '')
            cls.name_plural = '%ss' % cls.name
        return cls.name, cls.name_plural

    @classmethod
    def get_view(cls, name):
        """Формирует и возвращает объект представления.

        :param name:
        :return:
        """
        view_attr_name = 'view_%s' % name
        view = getattr(cls, view_attr_name)
        if view is None:
            realm_name, _ = cls.get_names()
            base_view_class = getattr(cls, 'view_%s_base_class' % name)
            class_dict = {
                'realm': cls,
                'name': name
            }
            view = type('%s%sView' % (realm_name.capitalize(), name.capitalize()), (base_view_class,), class_dict)
            setattr(cls, view_attr_name, view)
        return view

    @classmethod
    def get_syndication_url(cls):
        """Возвращает URL потока синдикации (RSS).

        :return:
        """
        if cls.syndication_url is None:
            cls.syndication_url = reverse('%s:syndication' % cls.name_plural)
        return cls.syndication_url

    @classmethod
    def get_urls(cls):
        """Вовзвращает набор URL, актуальных для этой области.

        :return:
        """
        views = ['']
        for view_name in cls.allowed_views:
            views.append(url(getattr(cls, 'view_%s_url' % view_name), cls.get_view(view_name).as_view(), name=view_name))

        if cls.syndication_enabled:
            views.append(url(r'^feed/$', cls.get_syndication_feed(), name='syndication'))

        _, realm_name_plural = cls.get_names()
        return patterns('', url(r'^%s/' % realm_name_plural, (patterns(*views), realm_name_plural, realm_name_plural)))
