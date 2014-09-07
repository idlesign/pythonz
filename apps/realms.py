from django.conf.urls import patterns, url

from sitetree.sitetreeapp import register_dynamic_trees, compose_dynamic_tree
from sitetree.utils import tree, item

from .generics.realms import RealmBase
from .models import User, Opinion, Book, Video, Event, Place, Article
from .forms import BookForm, VideoForm, EventForm, UserForm, OpinionForm, ArticleForm
from .signals import signal_new_entity, signal_entity_published
from .utils import notify_new_entity, notify_entity_published
from .zen import *  # Регистрируем блок сайта с дзеном


def bootstrap_realms(urlpatterns):
    """Инициализирует машинерию областей сайта.

    Принимает на вход urlpatterns из urls.py и модифицирует их.

    :param urlpatterns:
    :return:
    """
    urlpatterns += get_realms_urls()
    connect_signals()
    build_sitetree()
    return urlpatterns


REALMS_REGISTRY = []


def connect_signals():
    """Подключает обработчки сигналов проекта.

    :return:
    """
    notify_handler = lambda sender, **kwargs: notify_new_entity(kwargs['entity'])
    signal_new_entity.connect(notify_handler, dispatch_uid='cfg_new_entity', weak=False)

    notify_handler = lambda sender, **kwargs: notify_entity_published(kwargs['entity'])
    signal_entity_published.connect(notify_handler, dispatch_uid='cfg_entity_published', weak=False)


def register_realms(*classes):
    """Регистрирует области (сущности), которые должны быть доступны на сайте.

    :param classes:
    :return:
    """
    for cls in classes:
        REALMS_REGISTRY.append(cls)


def get_realms():
    """Возвращает список зарегистрированных областей сайта.

    :return:
    """
    return REALMS_REGISTRY


def get_sitemaps():
    """Возвращает словарь с sitemap-директивами для поисковых систем.

    :return:
    """
    sitemaps = {}
    for realm in get_realms():
        if realm.sitemap_enabled:
            sitemaps[realm.name_plural] = realm.get_sitemap()
    return sitemaps


def get_realms_urls():
    """Возвращает url-шаблоны всех зарегистрированных областей сайта.

    :return:
    """
    url_patterns = []
    for realm in get_realms():
        url_patterns += realm.get_urls()
    sitemaps = get_sitemaps()
    if sitemaps:
        url_patterns += patterns('', url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}))
    return url_patterns


def build_sitetree():
    """Строит древо сайта, исходя из достпных областей сайта.

    :return:
    """
    register_dynamic_trees(
        compose_dynamic_tree((
            tree('main', 'Основное дерево', (
                item('PYTHONZ', '/', alias='topmenu', url_as_pattern=False, children=(realm.get_sitetree_items() for realm in get_realms())),
                item('Вход', 'login', access_guest=True, in_menu=False, in_breadcrumbs=False),
                item('Личное меню', '#', alias='personal', url_as_pattern=False, access_loggedin=True, in_menu=False, in_sitetree=False, children=(
                    item('Профиль', 'users:details request.user.id', access_loggedin=True, in_breadcrumbs=False, in_sitetree=False),
                    item('Настройки', 'users:edit request.user.id', access_loggedin=True, in_breadcrumbs=False, in_sitetree=False),
                    item('Выход', 'logout', access_loggedin=True, in_breadcrumbs=False, in_sitetree=False),
                )),

            )),
            tree('about', 'О проекте', (
                item('Что такое Python', '/promo/', url_as_pattern=False),
                item('О проекте', '/about/', url_as_pattern=False),
                item('Карта сайта', '/sitemap/', url_as_pattern=False),
            ))
        ))
    )


class BookRealm(RealmBase):
    """
    Область с книгами.
    """

    model = Book
    form = BookForm
    icon = 'book'


class VideoRealm(RealmBase):
    """
    Область с видео.
    """

    model = Video
    form = VideoForm
    icon = 'film'


# class EventRealm(RealmBase):
#     """
#     Область с событиями.
#     """
#
#     model = Event
#     form = EventForm
#     icon = 'calendar'
#     sitemap_changefreq = 'daily'


# class OpeningRealm(RealmBase):
#
#     model = Opening
#     form = VideoForm
#     icon = 'briefcase'


class ArticleRealm(RealmBase):
    """
    Область со статьями.
    """

    model = Article
    form = ArticleForm
    icon = 'file'
    sitemap_changefreq = 'monthly'


# class PlaceRealm(RealmBase):
#     """
#     Область с [географическими] местами.
#     """
#
#     model = Place
#     form = VideoForm
#     icon = 'globe'


class OpinionRealm(RealmBase):
    """
    Область со мнениями.
    """

    model = Opinion
    form = OpinionForm
    icon = 'comment'
    allowed_views = ('listing', 'details', 'edit')
    syndication_enabled = False

    @classmethod
    def get_sitetree_details_item(cls):
        return item('{{ opinion.submitter.get_display_name }} про «{{ opinion.linked_object.title }}»', 'opinions:details opinion.id', children=(cls.get_sitetree_edit_item(),), in_menu=False, in_sitetree=False)


class UserRealm(RealmBase):
    """
    Область с персоналиями.
    """

    model = User
    form = UserForm
    icon = 'user'
    allowed_views = ('listing', 'details', 'edit')
    syndication_enabled = False
    sitemap_date_field = 'date_joined'
    sitemap_changefreq = 'daily'

    @classmethod
    def get_sitetree_details_item(cls):
        return item('{{ user.get_display_name }}', 'users:details user.id', in_menu=False, in_sitetree=False)


register_realms(BookRealm, VideoRealm, ArticleRealm, UserRealm, OpinionRealm)
