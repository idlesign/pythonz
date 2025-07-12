from django.http import HttpResponse
from django.shortcuts import redirect

from ..generics.views import DetailsView, HttpRequest, RealmView


class ReferenceListingView(RealmView):
    """Представление со списком справочников."""

    def get(self, request: HttpRequest) -> HttpResponse:
        # Справочник один, поэтому перенаправляем сразу на него.
        return redirect(self.realm.get_details_urlname(slugged=True), 'python', permanent=True)


class ReferenceDetailsView(DetailsView):
    """Представление статьи справочника."""

    def update_context(self, context: dict, request: HttpRequest):

        reference = context['item']
        context['children'] = reference.get_actual(parent=reference).order_by('title')

        if reference.parent is not None:
            context['siblings'] = reference.get_actual(
                parent=reference.parent, exclude_id=reference.id).order_by('title')
