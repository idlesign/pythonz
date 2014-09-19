from django.conf import settings
from django.conf.urls import patterns, url

from sitetree.utils import tree, item
# from sitecats.models import Category

from .forms import BookForm, VideoForm, EventForm, UserForm, OpinionForm, ArticleForm
from .generics.realms import RealmBase
from .models import User, Opinion, Book, Video, Event, Place, Article
from .signals import signal_new_entity, signal_entity_published
from .views_custom import UserDetailsView
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
    from .utils import notify_new_entity, notify_entity_published  # Потакаем поведению Django 1.7 при загрузке приложений.
    notify_handler = lambda sender, **kwargs: notify_new_entity(kwargs['entity'])
    signal_new_entity.connect(notify_handler, dispatch_uid='cfg_new_entity', weak=False)

    if settings.DEBUG:  # На всякий случай, чем чёрт не шутит.
        return False

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
    from sitetree.sitetreeapp import register_dynamic_trees, compose_dynamic_tree  # Потакаем поведению Django 1.7 при загрузке приложений.
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

    txt_promo = 'Времена и люди сменяют друг друга, а книги остаются. Взгляните на них &#8211; фолианты, книжицы и книжонки. Ходят слухи, что здесь можно отыскать даже гримуары.'
    txt_form_add = 'Добавить книгу'
    txt_form_edit = 'Изменить данные книги'

    model = Book
    form = BookForm
    icon = 'book'


class VideoRealm(RealmBase):
    """
    Область с видео.
    """

    txt_promo = 'Видео уникально в плане возможностей по усвоению материала: оно заставляет смотреть, слушать, и даже читать. Попробуйте, вам должно понравится.'
    txt_form_add = 'Добавить видео'
    txt_form_edit = 'Изменить данные видео'

    model = Video
    form = VideoForm
    icon = 'film'


# class EventRealm(RealmBase):
#     """
#     Область с событиями.
#     """
#
#     txt_promo = 'События разнообразят жизнь: встречи, лекции, беседы, обмен опытом позволяют расширить кругозор, установить связи, приятно провести время. Приобщайтесь.'
#     txt_form_add = 'Добавить событие'
#     txt_form_edit = 'Изменить событие'
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

    txt_promo = 'Статьи похожи на рассказы. Хорошие статьи, как и хорошие рассказы, хочется читать часто, много и даже с наслаждением.'
    txt_form_add = 'Написать статью'
    txt_form_edit = 'Редактировать статью'

    model = Article
    form = ArticleForm
    icon = 'file'
    sitemap_changefreq = 'monthly'


# class PlaceRealm(RealmBase):
#     """
#     Область с [географическими] местами.
#     """
#     txt_promo = 'В какую точку земного шара ни ткни, почти наверняка там найдутся интересные люди. Отправлятесь искать клад.'
#
#     model = Place
#     form = VideoForm
#     icon = 'globe'


class OpinionRealm(RealmBase):
    """
    Область со мнениями.
    """

    txt_promo = 'Мнения отражают картину мира людей. Делитесь своим, уважайте чужое. Добро пожаловать в картинную галерею.'
    txt_form_add = 'Добавить мнение'
    txt_form_edit = 'Изменить мнение'

    model = Opinion
    form = OpinionForm
    icon = 'comment'
    allowed_views = ('listing', 'details', 'edit')
    syndication_enabled = False


class UserRealm(RealmBase):
    """
    Область с персоналиями.
    """

    txt_promo = 'Вокруг люди &#8211; это они пишут статьи и книги, организовывают встречи и делятся мнениями, это они могут помочь, подсказать, научить. Здесь упомянуты некоторые.'
    txt_form_edit = 'Изменить настройки'

    model = User
    form = UserForm
    icon = 'user'
    allowed_views = ('listing', 'details', 'edit')
    syndication_enabled = False
    sitemap_date_field = 'date_joined'
    sitemap_changefreq = 'daily'
    view_details_base_class = UserDetailsView

    @classmethod
    def get_sitetree_details_item(cls):
        return item('{{ user.get_display_name }}', 'users:details user.id', in_menu=False, in_sitetree=False)


# class CategoryRealm(RealmBase):
#     """
#     Область с категориями.
#     """
#
#     txt_promo = 'Если всё разложить по полочкам, вероятность найти нужное возрастает. На наших полочках сплошь нужные вещи.'
#
#     model = Category
#     icon = 'tags'
#     name = 'category'
#     name_plural = 'categories'
#     allowed_views = ('listing', 'details')
#     ready_for_digest = False
#     sitemap_enabled = False  # TODO
#     syndication_enabled = False  # TODO


register_realms(BookRealm, VideoRealm, ArticleRealm, UserRealm, OpinionRealm)
