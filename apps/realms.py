from collections import OrderedDict
from operator import attrgetter

from django.db.models import signals
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse, get_resolver

from sitetree.utils import tree, item
from sitecats.toolbox import get_tie_model, get_category_model

from .forms.forms import BookForm, VideoForm, UserForm, DiscussionForm, ArticleForm, CommunityForm, EventForm, \
    ReferenceForm
from .generics.realms import RealmBase, SYNDICATION_URL_MARKER, SYNDICATION_ITEMS_LIMIT
from .generics.models import RealmBaseModel
from .models import User, Discussion, Book, Video, Place, Article, Community, Event, Reference, Vacancy
from .signals import sig_support_changed
from .views import UserDetailsView, CategoryListingView, PlaceListingView, PlaceDetailsView, UserEditView, \
    ReferenceListingView, ReferenceDetailsView, VacancyListingView
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


REALMS_REGISTRY = OrderedDict()


def connect_signals():
    """Подключает обработчки сигналов проекта.

    :return:
    """
    sig_support_changed.connect(RealmBaseModel.cache_delete_most_voted_objects)


def register_realms(*classes):
    """Регистрирует области (сущности), которые должны быть доступны на сайте.

    :param classes:
    :return:
    """
    for cls in classes:
        REALMS_REGISTRY[cls.get_names()[0]] = cls
        cls.init()


def get_realms():
    """Возвращает словарь зарегистрированных областей сайта,
    индексированный именами областей.

    :return:
    """
    return REALMS_REGISTRY


def get_realm(name):
    """Вернёт объет области по её имени, либо None.

    :param str name:
    :return:
    """
    realms = get_realms()
    realm = None

    try:
        realm = realms[name]
    except KeyError:
        pass

    return realm


def get_sitemaps():
    """Возвращает словарь с sitemap-директивами для поисковых систем.

    :return:
    """
    sitemaps = {}
    for realm in get_realms().values():
        if realm.sitemap_enabled:
            sitemaps[realm.name_plural] = realm.get_sitemap()
    return sitemaps


def get_realms_urls():
    """Возвращает url-шаблоны всех зарегистрированных областей сайта.

    :return:
    """
    url_patterns = []
    for realm in get_realms().values():
        url_patterns += realm.get_urls()
    sitemaps = get_sitemaps()
    if sitemaps:
        url_patterns += patterns(
            '', url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}))
    return url_patterns


def build_sitetree():
    """Строит древо сайта, исходя из доступных областей сайта.

    :return:
    """
    # Потакаем поведению Django 1.7 при загрузке приложений.
    from sitetree.sitetreeapp import register_dynamic_trees, compose_dynamic_tree
    register_dynamic_trees(
        compose_dynamic_tree((
            tree('main', 'Основное дерево', (
                item('Про Python', '/', alias='topmenu', url_as_pattern=False,
                     description='Сайт про Питон. Здесь можно найти различные материалы по языку программирования '
                                 'Python: книги, видео, справочник, сообщества, события, обсуждения и многое другое.',
                     children=(realm.get_sitetree_items() for realm in get_realms().values())),
                item('Вход', 'login', access_guest=True, in_menu=False, in_breadcrumbs=False),
                item('Личное меню', '#', alias='personal', url_as_pattern=False, access_loggedin=True, in_menu=False,
                     in_sitetree=False, children=(
                        item('Профиль', 'users:details request.user.id', access_loggedin=True, in_breadcrumbs=False,
                             in_sitetree=False),
                        item('Настройки', 'users:edit request.user.id', access_loggedin=True, in_breadcrumbs=False,
                             in_sitetree=False),
                        item('Выход', 'logout', access_loggedin=True, in_breadcrumbs=False, in_sitetree=False),
                )),

            )),
            tree('about', 'О проекте', (
                item('Что такое Python', '/promo/', description='Краткие сведения о языке программирования Python.',
                     url_as_pattern=False),
                item('О проекте', '/about/', description='Информация о проекте.', url_as_pattern=False),
                item('Карта сайта', '/sitemap/', description='Список разделов на сайте.',
                     url_as_pattern=False),
                item('Поиск по сайту', '/search/site/', url_as_pattern=False),
                item('Результаты поиска «{{ search_term }}»', '/search/', url_as_pattern=False, in_menu=False,
                     in_sitetree=False),
            ))
        )),
        reset_cache=True
    )


class BookRealm(RealmBase):
    """
    Область с книгами.
    """

    txt_form_add = 'Добавить книгу'
    txt_form_edit = 'Изменить данные книги'

    view_listing_description = 'Книги по программированию на языке Python. И просто книги по программированию.'
    view_listing_keywords = 'книги по питону, литература по python'

    model = Book
    form = BookForm
    icon = 'book'

    yawidget_code = 173166


class VideoRealm(RealmBase):
    """
    Область с видео.
    """

    txt_form_add = 'Добавить видео'
    txt_form_edit = 'Изменить данные видео'

    view_listing_description = 'Видео. Лекции, курсы, доклады, связанные с языком программирования Python.'
    view_listing_keywords = 'видео по питону, доклады по python'

    model = Video
    form = VideoForm
    icon = 'film'

    yawidget_code = 173167


class EventRealm(RealmBase):
    """
    Область с событиями.
    """

    view_listing_description = 'События. Встречи, конференции, спринты, круглые столы.'
    view_listing_keywords = 'конференции по питону, встречи сообществ python'

    txt_form_add = 'Добавить событие'
    txt_form_edit = 'Изменить событие'

    model = Event
    form = EventForm
    icon = 'calendar'
    sitemap_changefreq = 'daily'


class VacancyRealm(RealmBase):
    """
    Область с вакансиями.
    """

    allowed_views = ('listing',)
    name_plural = 'vacancies'

    view_listing_description = 'Вакансии, связанные с языком программирования Python.'
    view_listing_keywords = 'вакансии python, работа итон'

    view_listing_base_class = VacancyListingView

    model = Vacancy
    icon = 'briefcase'
    sitemap_changefreq = 'daily'
    sitemap_date_field = 'time_published'

    yawidget_code = 178839


class ReferenceRealm(RealmBase):
    """
    Область со справочниками.
    """

    allowed_views = ('listing', 'details', 'add', 'edit')
    syndication_enabled = False

    txt_form_add = 'Дополнить справочник'
    txt_form_edit = 'Редактировать статью'

    view_listing_description = 'Справочные материалы по языку программирования Python.'
    view_listing_keywords = 'справочник питон, руководство python'

    view_listing_base_class = ReferenceListingView
    view_details_base_class = ReferenceDetailsView

    model = Reference
    form = ReferenceForm
    icon = 'search'


class ArticleRealm(RealmBase):
    """
    Область со статьями.
    """

    txt_form_add = 'Написать статью'
    txt_form_edit = 'Редактировать статью'

    view_listing_description = 'Статьи, связанные с языком программирования Python.'
    view_listing_keywords = 'статьи о питоне, материалы по python'

    model = Article
    form = ArticleForm
    icon = 'file'

    yawidget_code = 173163


class PlaceRealm(RealmBase):
    """
    Область с географическими объектами (местами).
    """

    view_listing_description = 'Места, так или иначе связанные с языком программирования Python.'
    view_listing_keywords = 'python в городе, где программируют на питоне'

    model = Place
    form = VideoForm
    icon = 'picture'
    allowed_views = ('listing', 'details')
    sitemap_changefreq = 'monthly'
    view_listing_base_class = PlaceListingView
    view_details_base_class = PlaceDetailsView
    show_on_main = False


class DiscussionRealm(RealmBase):
    """
    Область обсуждений.
    """

    txt_form_add = 'Создать обсуждение'
    txt_form_edit = 'Редактировать обсуждение'

    view_listing_description = 'Обсуждения тем, связанных с программированием на pythonz.net.'
    view_listing_keywords = 'вопросы по питону, обсуждения python'

    model = Discussion
    form = DiscussionForm
    icon = 'list'


class UserRealm(RealmBase):
    """
    Область с персоналиями.
    """

    txt_form_edit = 'Изменить настройки'

    view_listing_description = 'Люди, связанные с языком программирования Python.'
    view_listing_keywords = 'питонисты, разработчики python'

    model = User
    form = UserForm
    icon = 'user'
    allowed_views = ('listing', 'details', 'edit')
    syndication_enabled = False
    sitemap_date_field = 'date_joined'
    view_details_base_class = UserDetailsView
    view_edit_base_class = UserEditView
    show_on_main = False

    @classmethod
    def get_sitetree_details_item(cls):
        return item('{{ user.get_display_name }}', 'users:details user.id', in_menu=False, in_sitetree=False)


class CategoryRealm(RealmBase):
    """
    Область с категориями.
    """

    view_listing_description = ('Категории материалов, связанных с языком программирования Python, '
                                'представленных на pythonz.net.')
    view_listing_keywords = 'материалы по питону, python по категориям'

    model = get_category_model()
    icon = 'tag'
    name = 'category'
    name_plural = 'categories'
    allowed_views = ('listing', 'details')
    ready_for_digest = False
    sitemap_enabled = False
    show_on_main = False
    view_listing_title = 'Путеводитель'
    view_listing_base_class = CategoryListingView
    view_details_base_class = CategoryListingView

    SYNDICATION_NAMESPACE = 'category_feeds'

    @classmethod
    def get_sitetree_details_item(cls):
        return item(
            'Категория «{{ category.parent.title }} — {{ category.title }}»', 'categories:details category.id',
            in_menu=False, in_sitetree=False)

    @classmethod
    def init(cls):
        # Включаем прослушивание сигналов, необходимое для функционировая области.
        tie_model = get_tie_model()
        # url-синдикации будут обновлены в случае добавления/удаления связи сущности с категорией.
        signals.post_save.connect(cls.update_syndication_urls, sender=tie_model)
        signals.post_delete.connect(cls.update_syndication_urls, sender=tie_model)

    @classmethod
    def get_urls(cls):
        urls = super().get_urls()
        urls += CategoryRealm.get_syndication_urls()
        return urls

    @classmethod
    def get_syndication_url(cls):
        return 'feed/'

    @classmethod
    def update_syndication_urls(cls, **kwargs):
        """Обновляет url-шаблоны синдикации, заменяя старые новыми."""
        target_namespace = cls.SYNDICATION_NAMESPACE
        linked_category_id_str = 'category_%s' % kwargs['instance'].category_id
        pattern_idx = -1

        resolver = get_resolver(None)
        urlpatterns = getattr(resolver.urlconf_module, 'urlpatterns', resolver.urlconf_module)

        for idx, pattern in enumerate(urlpatterns):
            if getattr(pattern, 'namespace', '') == target_namespace:
                pattern_idx = idx
                if linked_category_id_str in pattern.reverse_dict.keys():
                    # Категория была известна и ранее, перепривязка URL не требуется.
                    return
                break

        if pattern_idx > -1:
            del urlpatterns[pattern_idx]
            urlpatterns += cls.get_syndication_urls()

    @classmethod
    def get_syndication_urls(cls):
        """Возвращает url-шаблоны с привязанными сгенерированными представлениями
         для потоков синдикации (RSS) с перечислением новых материалов в категориях.

        :return:
        """
        feeds = []
        tie_model = get_tie_model()
        categories = tie_model.get_linked_objects(by_category=True)

        def get_in_category(category_id):
            """Возвращает объекты из разных областей в указанной категории."""
            linked = tie_model.get_linked_objects(filter_kwargs={'category_id': category_id}, id_only=True)
            result = []
            for model, ids in linked.items():
                result.extend(model.get_actual().filter(id__in=ids)[:SYNDICATION_ITEMS_LIMIT])
            result = sorted(result, key=attrgetter('time_published'), reverse=True)
            return result[:SYNDICATION_ITEMS_LIMIT]

        for category in categories.keys():
            title = category.title
            category_id = category.id
            feed = RealmBase._get_syndication_feed(
                title=title,
                description='Материалы в категории «%s». %s' % (title, category.note),
                func_link=lambda self: reverse(CategoryRealm.get_details_urlname(), args=[self.category_id]),
                func_items=lambda self: get_in_category(self.category_id),
                cls_name='Category%s' % category_id
            )
            feed.category_id = category_id

            feeds.append(
                url(r'^%s/%s/$' % (category_id, SYNDICATION_URL_MARKER), feed, name='category_%s' % category_id))

        _, realm_name_plural = CategoryRealm.get_names()

        return patterns(
            '', url(r'^%s/' % realm_name_plural, (patterns('', *feeds), realm_name_plural, cls.SYNDICATION_NAMESPACE)))


class CommunityRealm(RealmBase):
    """
    Область с сообществами.
    """

    txt_form_add = 'Зарегистрировать сообщество'
    txt_form_edit = 'Редактировать сообщество'

    view_listing_description = 'Сообщества людей интересующихся и занимающихся программированием на языке Python.'
    view_listing_keywords = 'сообщества питонистов, программисты python'

    name = 'community'
    name_plural = 'communities'
    model = Community
    form = CommunityForm
    icon = 'home'
    sitemap_changefreq = 'daily'


register_realms(
    CategoryRealm,
    BookRealm,
    VideoRealm,
    ArticleRealm,
    ReferenceRealm,
    EventRealm,
    VacancyRealm,
    UserRealm,
    PlaceRealm,
    DiscussionRealm,
    CommunityRealm
)
