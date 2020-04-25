from ..generics.views import DetailsView, HttpRequest


class PersonDetailsView(DetailsView):
    """Представление с детальной информацией о персоне."""

    def update_context(self, context: dict, request: HttpRequest):
        user = context['item']
        context['materials'] = lambda: user.get_materials()  # Ленивость для кеша в шаблоне
