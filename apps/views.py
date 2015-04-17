from sitegate.decorators import signin_view, signup_view, redirect_signedin
from sitegate.signup_flows.classic import SimpleClassicWithEmailSignup
from sitecats.toolbox import get_category_model, get_category_lists, get_category_aliases_under
from sitemessage.toolbox import get_user_preferences_for_ui, set_user_preferences_from_request
from xross.toolbox import xross_view
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.defaults import (
    page_not_found as dj_page_not_found,
    permission_denied as dj_permission_denied,
    server_error as dj_server_error
)

from .generics.views import DetailsView, RealmView, EditView
from .models import Place, User, Community, Event
from .exceptions import RedirectRequired


class UserDetailsView(DetailsView):
    """Представление с детальной информацией о пользователе."""

    get_object_related_fields = ['place']

    def _update_context(self, context, request):
        user = context['item']
        context['bookmarks'] = user.get_bookmarks()  # TODO проверить наполнение, возможно убрать области без закладок


class UserEditView(EditView):
    """Представление редактирования пользователя."""

    get_object_related_fields = ['last_editor']

    def check_edit_permissions(self, request, item):
        # Пользователи не могут редактировать других пользователей.
        if item != request.user:
            raise PermissionDenied()

    def _update_context(self, context, request):

        if request.POST:
            prefs_were_set = set_user_preferences_from_request(request)
            if prefs_were_set:
                raise RedirectRequired()

        subscr_prefs = get_user_preferences_for_ui(request.user, new_messengers_titles={
            'twitter': '<i class="fi-social-twitter" title="Twitter"></i>',
            'smtp': '<i class="fi-mail" title="Эл. почта"></i>'
        }, message_filter=lambda m: m.alias == 'digest')

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

    def _update_context(self, context, request):
        place = context['item']

        if request.user.is_authenticated():
            context['allow_im_here'] = (request.user.place != place)

        context['users'] = User.get_actual().filter(place=place)
        context['communities'] = Community.get_actual().filter(place=place)
        context['events'] = Event.get_actual().filter(place=place)


class PlaceListingView(RealmView):
    """Представление с картой и списком всех известных мест."""

    def get(self, request):
        places = Place.get_actual().order_by('-supporters_num', 'title')
        return self.render(request, {self.realm.name_plural: places})


class ReferenceListingView(RealmView):
    """Представление со списком справочников."""

    def get(self, request):
        # Справочник один, поэтому перенаправляем сразу на него.
        return redirect(self.realm.get_details_urlname(), 1, permanent=True)


class ReferenceDetailsView(DetailsView):
    """Представление статьи справочника."""

    get_object_related_fields = ['parent', 'submitter']

    def _update_context(self, context, request):
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
permission_denied = lambda request: dj_permission_denied(request, template_name='static/403.html')
page_not_found = lambda request: dj_page_not_found(request, template_name='static/404.html')
server_error = lambda request: dj_server_error(request, template_name='static/500.html')


def index(request):
    return redirect('categories:listing')


@redirect_signedin
@signin_view(widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label}, template='form_bootstrap3')
@signup_view(widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label}, template='form_bootstrap3',
             flow=SimpleClassicWithEmailSignup, verify_email=True)
def login(request):
    return render(request, 'static/login.html')
