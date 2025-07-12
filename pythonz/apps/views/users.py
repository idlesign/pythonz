from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from sitemessage.toolbox import get_user_preferences_for_ui, set_user_preferences_from_request

from ..exceptions import RedirectRequired
from ..generics.views import DetailsView, EditView, HttpRequest
from ..models import User


class UserDetailsView(DetailsView):
    """Представление с детальной информацией о пользователе."""

    def check_view_permissions(self, request: HttpRequest, item: User):
        super().check_view_permissions(request, item)

        if not item.profile_public and item != request.user:
            # Закрываем доступ к непубличным профилям.
            raise PermissionDenied

    def update_context(self, context: dict, request: HttpRequest):

        user = context['item']
        context['bookmarks'] = user.get_bookmarks()
        context['stats'] = lambda: user.get_stats()  # Ленивость для кеша в шаблоне

        if user == request.user:
            context['drafts'] = user.get_drafts()


class UserEditView(EditView):
    """Представление редактирования пользователя."""

    def check_edit_permissions(self, request: HttpRequest, item: User):
        # Пользователи не могут редактировать других пользователей.
        if item != request.user:
            raise PermissionDenied

    def update_context(self, context: dict, request: HttpRequest):

        if request.POST:
            prefs_were_set = set_user_preferences_from_request(request)

            if prefs_were_set:
                raise RedirectRequired

        subscr_prefs = get_user_preferences_for_ui(request.user, new_messengers_titles={
            'twitter': '<i class="fi-social-twitter" title="Twitter"></i>',
            'smtp': '<i class="fi-mail" title="Эл. почта"></i>'
        })

        context['subscr_prefs'] = subscr_prefs


@login_required
def user_settings(request: HttpRequest) -> HttpResponse:
    """Перенаправляет на страницу настроек текущего пользователя."""
    return redirect('users:edit', request.user.pk)
