from ..generics.views import DetailsView, HttpRequest


class VersionDetailsView(DetailsView):
    """Представление с детальной информацией о версии Питона."""

    def update_context(self, context: dict, request: HttpRequest):
        version = context['item']
        context['added'] = version.reference_added.order_by('title')
        context['deprecated'] = version.reference_deprecated.order_by('title')
        context['peps'] = version.peps.order_by('num')
