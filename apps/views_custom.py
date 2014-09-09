from .generics.views import DetailsView
from django.views.defaults import page_not_found as dj_page_not_found, permission_denied as dj_permission_denied, server_error as dj_server_error


class UserDetailsView(DetailsView):
    """Перекрываем представление с детальной информацией для пользователей,
    чтобы поместить в контекст шаблона дополнительную информацию."""

    def _update_context(self, context):
        user = context['item']
        context['bookmarks'] = user.get_bookmarks()


# Наши страницы ошибок.
permission_denied = lambda request: dj_permission_denied(request, template_name='static/403.html')
page_not_found = lambda request: dj_page_not_found(request, template_name='static/404.html')
server_error = lambda request: dj_server_error(request, template_name='static/500.html')
