from sitegate.decorators import signin_view, signup_view, redirect_signedin
from sitegate.signup_flows.classic import SimpleClassicWithEmailSignup
from sitecats.toolbox import get_category_model, get_category_lists, get_category_aliases_under
from sitemessage.toolbox import get_user_preferences_for_ui, set_user_preferences_from_request
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


class UserDetailsView(DetailsView):
    """Представление с детальной информацией о пользователе."""

    def _update_context(self, context, request):
        user = context['item']
        context['bookmarks'] = user.get_bookmarks()  # TODO проверить наполнение, возможно убрать области без закладок

    def get_object_or_404(self, obj_id):
        return get_object_or_404(self.realm.model.objects.select_related('place'), pk=obj_id)


class UserEditView(EditView):
    """Представление редактирования пользователя."""

    def check_edit_permissions(self, request, item):
        # Пользователи не могут редактировать других пользователей.
        if item != request.user:
            raise PermissionDenied()

    def _update_context(self, context, request):

        # todo
        if request.POST:
            set_user_preferences_from_request(request)

        def message_filter(m):
            return m.alias == 'digest'

        subscr_prefs = get_user_preferences_for_ui(request.user, new_messengers_titles={
            'twitter': '<i class="fi-social-twitter" title="Twitter"></i>',
            'smtp': '<i class="fi-mail" title="Эл. почта"></i>'
        })#, message_filter=message_filter)
        #todo

        context['subscr_prefs'] = subscr_prefs


class PlaceDetailsView(DetailsView):
    """Представление с детальной информацией о месте."""

    def _update_context(self, context, request):
        place = context['item']
        context['users'] = User.get_actual().filter(place=place)
        context['communities'] = Community.get_actual().filter(place=place)
        context['events'] = Event.get_actual().filter(place=place)


class PlaceListingView(RealmView):
    """Представление с картой и списком всех известных мест."""

    def get(self, request):
        places = Place.get_actual().order_by('-supporters_num')
        return self.render(request, {self.realm.name_plural: places})


class ReferenceListingView(RealmView):
    """Представление со списком справочников."""

    def get(self, request):
        # Справочник один, поэтому перенаправляем сразу на него.
        return redirect(self.realm.get_details_urlname(), 1, permanent=True)


class ReferenceDetailsView(DetailsView):
    """Представление статьи справочника."""

    def _update_context(self, context, request):
        reference = context['item']
        context['children'] = reference.get_actual(reference).order_by('title')
        if reference.parent is not None:
            context['siblings'] = reference.get_actual(reference.parent, exclude_id=reference.id).order_by('title')

    def get_object_or_404(self, obj_id):
        return get_object_or_404(self.realm.model.objects.select_related('parent', 'submitter'), pk=obj_id)


class CategoryListingView(RealmView):
    """Выводит список известных категорий, либо список сущностей для конкретной категории."""

    def get(self, request, obj_id=None):
        from apps.realms import get_realms
        if obj_id is None:  # Запрошен список всех известных категорий.
            item = get_category_lists(
                init_kwargs={
                    'show_title': True,
                    'show_links': lambda cat: reverse(self.realm.get_details_urlname(), args=[cat.id])
                },
                additional_parents_aliases=get_category_aliases_under())
            return self.render(request, {'item': item})

        # Выводим список материалов (разбитых по областям сайта) для конкретной категории.
        category_model = get_category_model()
        category = get_object_or_404(category_model.objects.select_related('parent'), pk=obj_id)

        realm_list = []
        for realm in get_realms().values():
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
    from .realms import get_realms
    return render(request, 'index.html', {'realms': get_realms().values()})


@redirect_signedin
@signin_view(widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label}, template='form_bootstrap3')
@signup_view(widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label}, template='form_bootstrap3', flow=SimpleClassicWithEmailSignup, verify_email=True)
def login(request):
    return render(request, 'static/login.html')
