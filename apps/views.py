from itertools import groupby
from urllib.parse import quote_plus

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.defaults import (
    page_not_found as dj_page_not_found,
    permission_denied as dj_permission_denied,
    server_error as dj_server_error
)
from operator import attrgetter
from sitecats.toolbox import get_category_model, get_category_lists, get_category_aliases_under
from sitegate.decorators import signin_view, signup_view, redirect_signedin
from sitegate.signup_flows.classic import SimpleClassicWithEmailSignup
from sitemessage.toolbox import get_user_preferences_for_ui, set_user_preferences_from_request
from xross.toolbox import xross_view

from .integration.telegram import handle_request
from .exceptions import RedirectRequired
from .generics.views import DetailsView, RealmView, EditView, ListingView
from .models import Place, User, Community, Event, Reference, Vacancy, ExternalResource, ReferenceMissing
from .utils import message_warning
from .signals import sig_search_failed


class UserDetailsView(DetailsView):
    """Представление с детальной информацией о пользователе."""

    get_object_related_fields = ['place']

    def check_view_permissions(self, request, item):
        super().check_view_permissions(request, item)

        if not item.profile_public and item != request.user:
            # Закрываем доступ к непубличным профилям.
            raise PermissionDenied()

    def update_context(self, context, request):
        user = context['item']
        context['bookmarks'] = user.get_bookmarks()


class UserEditView(EditView):
    """Представление редактирования пользователя."""

    get_object_related_fields = ['last_editor']

    def check_edit_permissions(self, request, item):
        # Пользователи не могут редактировать других пользователей.
        if item != request.user:
            raise PermissionDenied()

    def update_context(self, context, request):

        if request.POST:
            prefs_were_set = set_user_preferences_from_request(request)
            if prefs_were_set:
                raise RedirectRequired()

        subscr_prefs = get_user_preferences_for_ui(request.user, new_messengers_titles={
            'twitter': '<i class="fi-social-twitter" title="Twitter"></i>',
            'smtp': '<i class="fi-mail" title="Эл. почта"></i>'
        })

        context['subscr_prefs'] = subscr_prefs


class PlaceDetailsView(DetailsView):
    """Представление с детальной информацией о месте."""

    get_object_related_fields = ['last_editor']

    def set_im_here(self, request, xross=None):
        """Используется xross. Прописывает место и часовой пояс в профиль пользователя.

        :param request:
        :param xross:
        :return:
        """
        user = request.user
        if user.is_authenticated():
            user.place = xross.attrs['item']
            user.set_timezone_from_place()
            user.save()

    @xross_view(set_im_here)  # Метод перекрыт для добавления AJAX-обработчика.
    def get(self, request, obj_id):
        return super().get(request, obj_id)

    def update_context(self, context, request):
        place = context['item']

        if request.user.is_authenticated():
            context['allow_im_here'] = (request.user.place != place)

        context['users'] = User.get_actual().filter(place=place)
        context['communities'] = Community.get_actual().filter(place=place)
        context['events'] = Event.get_actual().filter(place=place)
        context['vacancies'] = Vacancy.get_actual().filter(place=place)
        context['stats_salary'] = Vacancy.get_salary_stats(place)


class PlaceListingView(RealmView):
    """Представление с картой и списком всех известных мест."""

    def get(self, request):
        places = Place.get_actual().order_by('-supporters_num', 'title')
        return self.render(request, {self.realm.name_plural: places})


class VacancyListingView(ListingView):
    """Представление со списком вакансий."""

    get_object_related_fields = ['place']

    def update_context(self, context, request):
        context['stats_salary'] = Vacancy.get_salary_stats()
        context['stats_places'] = Vacancy.get_places_stats()

    def get_most_voted_objects(self):
        return []


class ReferenceListingView(RealmView):
    """Представление со списком справочников."""

    def get(self, request):
        # Справочник один, поэтому перенаправляем сразу на него.
        return redirect(self.realm.get_details_urlname(slugged=True), 'python', permanent=True)


class ReferenceDetailsView(DetailsView):
    """Представление статьи справочника."""

    get_object_related_fields = ['parent', 'submitter']

    def update_context(self, context, request):
        reference = context['item']
        context['children'] = reference.get_actual(reference).order_by('title')
        if reference.parent is not None:
            context['siblings'] = reference.get_actual(reference.parent, exclude_id=reference.id).order_by('title')


class CategoryListingView(RealmView):
    """Выводит список известных категорий, либо список сущностей для конкретной категории."""

    def get(self, request, obj_id=None):
        from apps.realms import get_realms
        realms = get_realms().values()

        if obj_id is None:  # Запрошен список всех известных категорий.
            item = get_category_lists(
                init_kwargs={
                    'show_title': True,
                    'show_links': lambda cat: reverse(self.realm.get_details_urlname(), args=[cat.id])
                },
                additional_parents_aliases=get_category_aliases_under())
            return self.render(request, {'item': item, 'realms': realms})

        # Выводим список материалов (разбитых по областям сайта) для конкретной категории.
        category_model = get_category_model()
        category = get_object_or_404(category_model.objects.select_related('parent'), pk=obj_id)

        realm_list = []
        for realm in realms:
            if hasattr(realm.model, 'categories'):  # ModelWithCategory
                objs = realm.model.get_objects_in_category(category)[:5]
                if objs:
                    realm_list.append({
                        'objects': objs,
                        'url': reverse(realm.get_tags_urlname(), args=[category.id]),
                        'realm': realm
                    })

        return self.render(request, {self.realm.name: category, 'item': category, 'realm_list': realm_list})


# Наши страницы ошибок.
permission_denied = lambda request, exception: dj_permission_denied(request, exception, template_name='static/403.html')
page_not_found = lambda request, exception: dj_page_not_found(request, exception, template_name='static/404.html')
server_error = lambda request: dj_server_error(request, template_name='static/500.html')


@cache_page(1800)  # 30 минут
def index(request):
    """Индексная страница."""
    from .realms import get_realms

    realms_data = []
    realms_registry = get_realms()

    externals = ExternalResource.objects.filter(realm_name__in=realms_registry.keys())
    externals = {k: list(v) for k, v in groupby(externals, attrgetter('realm_name'))}

    max_additional = 5

    for name, realm in realms_registry.items():
        if not realm.show_on_main:
            continue

        realm_externals = externals.get(name, [])
        count_externals = len(realm_externals)

        count_locals = 1
        if count_externals < max_additional:
            count_locals += max_additional - count_externals

        realm_locals = realm.model.get_actual()[:count_locals]

        main = realm_locals[0]
        additional = list(realm_locals[1:]) + realm_externals

        realms_data.append({
            'cls': realm,
            'main': main,
            'additional': additional,
        })

    return render(request, 'index.html', {'realms_data': realms_data})


@csrf_exempt
def telebot(request):
    """Обрабатывает запросы от Telegram.

    :param request:
    :rtype: HttpResponse
    """
    handle_request(request)
    return HttpResponse()


def search(request):
    """Страница с результатами поиска по справочнику.
    Если найден один результат, перенаправляет на страницу результата.

    """
    search_term = request.GET.get('search_term', '').strip(' ()')

    if not search_term:
        return redirect('index')

    results = Reference.find(search_term)
    total_results = len(results)

    if not total_results:
        # Поиск не дал результатов. Запомним, что искали и сообщим администраторам,
        # чтобы приняли меры по возможности.

        if ReferenceMissing.add(search_term):
            sig_search_failed.send(None, search_term=search_term)

        message_warning(request, 'Поиск по справочнику не дал результатов, и мы переключились на поиск по всему сайту.')

        # Перенаправляем на поиск по всему сайту.
        redirect_response = redirect('search_site')
        redirect_response['Location'] += '?searchid=%s&text=%s' % (settings.YANDEX_SEARCH_ID, quote_plus(search_term))
        return redirect_response

    elif total_results == 1:
        return redirect(results[0].get_absolute_url())

    return render(request, 'static/search.html', {'search_term': search_term, 'results': results})


@redirect_signedin
@signin_view(widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label}, template='form_bootstrap3')
@signup_view(widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label}, template='form_bootstrap3',
             flow=SimpleClassicWithEmailSignup, verify_email=True)
def login(request):
    """Страница авторизации и регистрации."""
    return render(request, 'static/login.html')
