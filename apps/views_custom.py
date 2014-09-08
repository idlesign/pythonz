from .generics.views import DetailsView


class UserDetailsView(DetailsView):
    """Перекрываем представление с детальной информацией для пользователей,
    чтобы поместить в контекст шаблона дополнительную информацию."""

    def _update_context(self, context):
        user = context['item']
        context['bookmarks'] = user.get_bookmarks()
