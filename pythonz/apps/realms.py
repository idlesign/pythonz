from collections.abc import Generator
from operator import attrgetter

from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap
from django.db.models import signals
from django.urls import get_resolver, path, re_path, reverse
from sitecats.toolbox import get_tie_model
from sitetree.models import TreeItemBase
from sitetree.sitetreeapp import compose_dynamic_tree, register_dynamic_trees
from sitetree.utils import item, tree

from .forms.forms import (
    AppForm,
    ArticleForm,
    BookForm,
    CommunityForm,
    DiscussionForm,
    EventForm,
    ReferenceForm,
    UserForm,
    VersionForm,
    VideoForm,
)
from .generics.forms import CommonEntityForm
from .generics.models import RealmBaseModel
from .generics.realms import SYNDICATION_ITEMS_LIMIT, SYNDICATION_URL_MARKER, RealmBase
from .generics.views import RealmView
from .models import (
    PEP,
    App,
    Article,
    Book,
    Category,
    Community,
    Discussion,
    Event,
    Person,
    Place,
    Reference,
    User,
    Vacancy,
    Version,
    Video,
)
from .signals import sig_support_changed
from .views import (
    CategoryListingView,
    PepListingView,
    PersonDetailsView,
    PlaceDetailsView,
    PlaceListingView,
    ReferenceDetailsView,
    ReferenceListingView,
    UserDetailsView,
    UserEditView,
    VacancyListingView,
    VersionDetailsView,
    ide,
)
from .zen import register_zen_siteblock

# Регистрируем блок сайта с дзеном
register_zen_siteblock()


def bootstrap_realms(urlpatterns: list) -> list:
    """Инициализирует машинерию областей сайта.

    Принимает на вход urlpatterns из urls.py и модифицирует их.

    :param urlpatterns:

    """
    urlpatterns += get_realms_urls()

    connect_signals()
    build_sitetree()

    return urlpatterns


REALMS_REGISTRY: dict[str, type[RealmBase]] = {}


def connect_signals():
    """Подключает обработчки сигналов проекта."""

    sig_support_changed.connect(RealmBaseModel.cache_delete_most_voted_objects)
    signals.post_save.connect(ReferenceRealm.build_sitetree, sender=Reference)
    signals.post_delete.connect(ReferenceRealm.build_sitetree, sender=Reference)


def register_realms(*classes: type[RealmBase]):
    """Регистрирует области (сущности), которые должны быть доступны на сайте.

    :param classes:

    """
    for cls in classes:
        REALMS_REGISTRY[cls.get_names()[0]] = cls
        cls.init()


def get_realms_models() -> list[type[RealmBaseModel]]:
    """Возвращает список моделей всех областей сайта."""
    return [r.model for r in get_realms().values()]


def get_realms() -> dict[str, type[RealmBase]]:
    """Возвращает словарь зарегистрированных областей сайта,
    индексированный именами областей.

    """
    return REALMS_REGISTRY


def get_realm(name: str) -> type[RealmBase] | None:
    """Вернёт область по её имени, либо None.

    :param name:

    """
    realms = get_realms()
    realm = None

    try:
        realm = realms[name]

    except KeyError:
        pass

    return realm


def get_sitemaps() -> dict[str, GenericSitemap]:
    """Возвращает словарь с sitemap-директивами для поисковых систем."""

    sitemaps = {}

    for realm in get_realms().values():

        if realm.sitemap_enabled:
            sitemaps[realm.name_plural] = realm.get_sitemap()

    return sitemaps


def get_realms_urls() -> list:
    """Возвращает url-шаблоны всех зарегистрированных областей сайта."""

    url_patterns = [
        path('references/ide/', ide),
    ]

    for realm in get_realms().values():
        url_patterns += realm.get_urls()

    if sitemaps := get_sitemaps():
        url_patterns += [re_path(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps})]

    return url_patterns


def get_sitetree_root_item(children: Generator[TreeItemBase] = None) -> TreeItemBase:
    """Возвращает корневой элемент динамического древа сайта.

    :param children: Дочерние динамические элементы.

    """
    return item(
        'Про Python', '/', alias='topmenu', url_as_pattern=False,
        description='Сайт про Питон. Различные материалы по языку программирования Python: '
                    'книги, видео, справочник, сообщества, события, обсуждения и многое другое.',
        children=children)


def build_sitetree():
    """Строит древо сайта, исходя из доступных областей сайта."""

    register_dynamic_trees(
        compose_dynamic_tree((
            tree('main', 'Основное дерево', (
                get_sitetree_root_item((realm.get_sitetree_items() for realm in get_realms().values())),
                item('Вход', 'login', access_guest=True, in_menu=False, in_breadcrumbs=False),
                item('', '/', alias='personal', url_as_pattern=False, access_loggedin=True, in_menu=False,
                     in_sitetree=False, children=(
                        item('Профиль', 'users:details request.user.id', access_loggedin=True, in_breadcrumbs=True,
                             in_sitetree=False),
                        item('Настройки', 'users:edit request.user.id', access_loggedin=True, in_breadcrumbs=True,
                             in_sitetree=False),
                        item('Выход', 'logout', access_loggedin=True, in_breadcrumbs=False, in_sitetree=False),
                )),

            )),
            tree('about', 'О проекте', (
                item('Что такое Python', '/promo/',
                     description='Краткие сведения о возможностях и областях применения языка программирования Python.',
                     url_as_pattern=False),
                item('О проекте', '/about/',
                     description='Информация о проекте. О том, как, кем и для чего разрабатывается данный сайт.',
                     url_as_pattern=False),
                item('Карта сайта', '/sitemap/', description='Список разделов на сайте оформленный в виде карты сайта.',
                     url_as_pattern=False),
                item('Поиск по сайту', '/search/site/',
                     description='Глобальный поиск по материалам, расположенным на сайте.',
                     url_as_pattern=False),
                item('Результаты поиска «{{ search_term }}»', '/search/', url_as_pattern=False, in_menu=False,
                     in_sitetree=False),
            ))
        )),
        reset_cache=True
    )

    ReferenceRealm.build_sitetree()


class BookRealm(RealmBase):
    """Область с книгами."""

    txt_form_add: str = 'Добавить книгу'
    txt_form_edit: str = 'Изменить книгу'

    view_listing_description: str = 'Книги по программированию вообще и на языке Python в частности.'
    view_listing_keywords: str = 'книги по питону, литература по python'

    model: type[RealmBaseModel] = Book
    form: type[CommonEntityForm] = BookForm
    icon: str = 'book'


class VideoRealm(RealmBase):
    """Область с видео."""

    txt_form_add: str = 'Добавить видео'
    txt_form_edit: str = 'Изменить видео'

    view_listing_description: str = 'Видео-записи лекций, курсов, докладов, связанные с языком программирования Python'
    view_listing_keywords: str = 'видео по питону, доклады по python'

    model: type[RealmBaseModel] = Video
    form: type[CommonEntityForm] = VideoForm
    icon: str = 'film'


class EventRealm(RealmBase):
    """Область с событиями."""

    view_listing_description: str = (
        'События, которые могут заинтересовать питонистов: встречи, конференции, спринты, и пр.')
    view_listing_keywords: str = 'конференции по питону, встречи сообществ python'

    txt_form_add: str = 'Добавить событие'
    txt_form_edit: str = 'Изменить событие'

    model: type[RealmBaseModel] = Event
    form: type[CommonEntityForm] = EventForm
    icon: str = 'calendar'


class VacancyRealm(RealmBase):
    """Область с вакансиями."""

    allowed_views: tuple[str, ...] = ('listing',)
    name_plural: str = 'vacancies'

    show_on_main: bool = False

    view_listing_description: str = 'Список вакансий, так или иначе связанных с языком программирования Python.'
    view_listing_keywords: str = 'вакансии python, работа питон'

    view_listing_base_class: type[RealmView] = VacancyListingView

    model: type[RealmBaseModel] = Vacancy
    icon: str = 'briefcase'
    sitemap_enabled: bool = False


class ReferenceRealm(RealmBase):
    """Область со справочниками."""

    allowed_views: tuple[str, ...] = ('listing', 'details', 'add', 'edit')

    txt_form_add: str = 'Дополнить справочник'
    txt_form_edit: str = 'Редактировать статью'

    view_listing_description: str = 'Справочные и обучающие материалы по языку программирования Python.'
    view_listing_keywords: str = 'справочник, питон, руководство, обучение, python 3, пайтон'

    view_listing_base_class: type[RealmView] = ReferenceListingView
    view_details_base_class: type[RealmView] = ReferenceDetailsView

    model: type[RealmBaseModel] = Reference
    form: type[CommonEntityForm] = ReferenceForm
    icon: str = 'search'

    @classmethod
    def build_sitetree(cls, **kwargs):
        """Строит динамическое дерево справочника под именем `references`."""
        root_id = object()

        root_item = get_sitetree_root_item()
        temp_ref_items = {root_id: root_item}

        ref_items = list(cls.model.get_actual().select_related('parent').only(
            'id', 'parent_id', 'parent__title', 'slug', 'status'
        ).order_by('parent_id', 'title', 'id'))

        def get_tree_item(ref_item):
            item_id = getattr(ref_item, 'id', root_id)
            tree_item = temp_ref_items.get(item_id)

            if not tree_item:
                tree_item = item(ref_item.title, ref_item.get_absolute_url(), url_as_pattern=False)
                temp_ref_items[item_id] = tree_item

            return tree_item

        for ref_item in ref_items:
            parent = get_tree_item(ref_item.parent)
            child = get_tree_item(ref_item)

            child.parent = parent
            parent.dynamic_children.append(child)

        register_dynamic_trees(compose_dynamic_tree([tree('references', items=[root_item])]), reset_cache=True)


class ArticleRealm(RealmBase):
    """Область со статьями."""

    txt_form_add: str = 'Добавить статью'
    txt_form_edit: str = 'Редактировать статью'

    view_listing_description: str = 'Статьи и заметки, связанные с программированием Python и не только.'
    view_listing_keywords: str = 'статьи про питон, материалы по python'

    model: type[RealmBaseModel] = Article
    form: type[CommonEntityForm] = ArticleForm
    icon: str = 'file-o'


class PlaceRealm(RealmBase):
    """Область с географическими объектами (местами)."""

    view_listing_description: str = 'Места, так или иначе связанные с языком программирования Python.'
    view_listing_keywords: str = 'python в городе, где программируют на питоне'

    view_listing_base_class: type[RealmView] = PlaceListingView
    view_details_base_class: type[RealmView] = PlaceDetailsView

    model: type[RealmBaseModel] = Place
    form: type[CommonEntityForm] = VideoForm
    icon: str = 'globe'

    sitemap_changefreq: str = 'weekly'
    allowed_views: tuple[str, ...] = ('listing', 'details')
    show_on_main: bool = False
    show_on_top: bool = False


class DiscussionRealm(RealmBase):
    """Область обсуждений."""

    txt_form_add: str = 'Создать обсуждение'
    txt_form_edit: str = 'Редактировать обсуждение'

    view_listing_description: str = 'Обсуждения вопросов, связанных с программированием на Питоне.'
    view_listing_keywords: str = 'вопросы по питону, обсуждения python, отзывы'

    model: type[RealmBaseModel] = Discussion
    form: type[CommonEntityForm] = DiscussionForm
    icon: str = 'comments-o'

    allowed_views: tuple[str, ...] = ('details', 'tags', 'add', 'edit')
    ready_for_digest: bool = False
    sitemap_enabled: bool = False
    syndication_enabled: bool = False

    show_on_main: bool = False
    show_on_top: bool = False


class UserRealm(RealmBase):
    """Область с пользователями сайта."""

    txt_form_edit: str = 'Изменить настройки'

    view_listing_description: str = 'Список пользователей сайта.'
    view_listing_keywords: str = 'питонисты, разработчики python, пользователи сайта'

    view_details_base_class: type[RealmView] = UserDetailsView
    view_edit_base_class: type[RealmView] = UserEditView

    model: type[RealmBaseModel] = User
    form: type[CommonEntityForm] = UserForm
    icon: str = 'users'

    sitemap_date_field: str = 'date_joined'
    sitemap_changefreq: str = 'weekly'
    allowed_views: tuple[str, ...] = ('details', 'edit')
    ready_for_digest: bool = False
    sitemap_enabled: bool = False
    syndication_enabled: bool = False

    show_on_main: bool = False
    show_on_top: bool = False

    @classmethod
    def get_sitetree_details_item(cls) -> TreeItemBase:
        return item('{{ user.get_display_name }}', 'users:details user.id', in_menu=False, in_sitetree=False)


class CategoryRealm(RealmBase):
    """Область с категориями."""

    view_listing_description: str = 'Карта категорий материалов по языку программирования Python доступных на сайте.'
    view_listing_keywords: str = 'материалы по питону, python по категориям'

    model: type[RealmBaseModel] = Category
    icon: str = 'tag'
    name: str = 'category'
    name_plural: str = 'categories'
    allowed_views: tuple[str, ...] = ('listing', 'details')
    ready_for_digest: bool = False
    sitemap_enabled: bool = False

    show_on_main: bool = False
    show_on_top: bool = False

    view_listing_title: str = 'Путеводитель'
    view_listing_base_class: type[RealmView] = CategoryListingView
    view_details_base_class: type[RealmView] = CategoryListingView

    SYNDICATION_NAMESPACE: str = 'category_feeds'

    @classmethod
    def get_sitetree_details_item(cls) -> TreeItemBase:
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
    def get_urls(cls) -> list:
        urls = super().get_urls()
        urls += CategoryRealm.get_syndication_urls()
        return urls

    @classmethod
    def get_syndication_url(cls) -> str:
        return 'feed/'

    @classmethod
    def update_syndication_urls(cls, **kwargs):
        """Обновляет url-шаблоны синдикации, заменяя старые новыми."""

        target_namespace = cls.SYNDICATION_NAMESPACE
        linked_category_id_str = f"category_{kwargs['instance'].category_id}"
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
    def get_syndication_urls(cls) -> list:
        """Возвращает url-шаблоны с привязанными сгенерированными представлениями
         для потоков синдикации (RSS) с перечислением новых материалов в категориях.

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
                description=f'Материалы в категории «{title}». {category.note}',
                func_link=lambda self: reverse(CategoryRealm.get_details_urlname(), args=[self.category_id]),
                func_items=lambda self: get_in_category(self.category_id),
                cls_name=f'Category{category_id}'
            )
            feed.category_id = category_id

            feeds.append(
                re_path(fr'^{category_id}/{SYNDICATION_URL_MARKER}/$', feed, name=f'category_{category_id}'))

        _, realm_name_plural = CategoryRealm.get_names()

        return [re_path(fr'^{realm_name_plural}/', (feeds, realm_name_plural, cls.SYNDICATION_NAMESPACE))]


class CommunityRealm(RealmBase):
    """Область с сообществами."""

    txt_form_add: str = 'Добавить сообщество'
    txt_form_edit: str = 'Редактировать сообщество'

    view_listing_description: str = 'Сообщества людей интересующихся и занимающихся программированием на Питоне.'
    view_listing_keywords: str = 'сообщества питонистов, программисты python'

    name: str = 'community'
    name_plural: str = 'communities'
    model: type[RealmBaseModel] = Community
    form: type[CommonEntityForm] = CommunityForm
    icon: str = 'building-o'

    show_on_main: bool = False
    show_on_top: bool = False


class VersionRealm(RealmBase):
    """Область с версиями."""

    txt_form_add: str = 'Добавить версию'
    txt_form_edit: str = 'Редактировать версию'

    view_listing_description: str = 'Вышедшие и будущие выпуски Python.'
    view_listing_keywords: str = 'версии python, выпуски Питона'

    allowed_views: tuple[str, ...] = ('listing', 'details', 'add', 'edit')
    view_details_base_class: type[RealmView] = VersionDetailsView

    name: str = 'version'
    name_plural: str = 'versions'
    model: type[RealmBaseModel] = Version
    form: type[CommonEntityForm] = VersionForm
    icon: str = 'code-fork'

    show_on_top: bool = False
    show_on_main: bool = False


class PepRealm(RealmBase):
    """Область с предложениями по улучшению."""

    view_listing_description: str = 'Предложения по улучшению Питона (PEP).'
    view_listing_keywords: str = 'python pep, преложения по улучшению, пепы, пеп'

    view_listing_base_class: type[RealmView] = PepListingView

    allowed_views: tuple[str, ...] = ('listing', 'details')

    name: str = 'pep'
    name_plural: str = 'peps'
    model: type[RealmBaseModel] = PEP

    icon: str = 'bell'

    show_on_top: bool = False


class PersonRealm(RealmBase):
    """Область персон."""

    view_listing_description: str = 'Персоны, тем или иным образом связанные с языком Python.'
    view_listing_keywords: str = 'персоны python, питонисты, разработчики python'

    allowed_views: tuple[str, ...] = ('listing', 'details')
    view_details_base_class: type[RealmView] = PersonDetailsView

    name: str = 'person'
    name_plural: str = 'persons'
    model: type[RealmBaseModel] = Person

    icon: str = 'user'

    show_on_main: bool = False
    show_on_top: bool = False

    syndication_enabled: bool = False
    ready_for_digest: bool = False


class AppRealm(RealmBase):
    """Область приложений."""

    txt_form_add: str = 'Добавить приложение'
    txt_form_edit: str = 'Редактировать приложение'

    view_listing_description: str = 'Приложения на Python.'
    view_listing_keywords: str = 'программы на python, приложения на питоне'

    name: str = 'app'
    name_plural: str = 'apps'

    model: type[RealmBaseModel] = App
    form: type[CommonEntityForm] = AppForm

    icon: str = 'tablet'

    show_on_top: bool = False


register_realms(
    CategoryRealm,
    ArticleRealm,
    ReferenceRealm,
    VideoRealm,
    BookRealm,
    VacancyRealm,
    EventRealm,

    PlaceRealm,
    DiscussionRealm,
    CommunityRealm,

    VersionRealm,
    PepRealm,
    PersonRealm,
    AppRealm,

    UserRealm,
)
