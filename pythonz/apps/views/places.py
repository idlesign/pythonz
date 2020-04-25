from django.http import HttpResponse
from xross.toolbox import xross_view
from xross.utils import XrossHandlerBase

from ..generics.views import DetailsView, RealmView, HttpRequest
from ..models import Place, User, Community, Event, Vacancy


class PlaceDetailsView(DetailsView):
    """Представление с детальной информацией о месте."""

    def set_im_here(self, request: HttpRequest, xross: XrossHandlerBase = None):
        """Используется xross. Прописывает место и часовой пояс в профиль пользователя.

        :param request:
        :param xross:

        """
        user = request.user

        if user.is_authenticated:
            user.place = xross.attrs['item']
            user.set_timezone_from_place()
            user.save()

    @xross_view(set_im_here)  # Метод перекрыт для добавления AJAX-обработчика.
    def get(self, request: HttpRequest, obj_id: int) -> HttpResponse:
        return super().get(request, obj_id)

    def update_context(self, context: dict, request: HttpRequest):
        place = context['item']

        if request.user.is_authenticated:
            context['allow_im_here'] = (request.user.place != place)

        context['users'] = User.get_actual().filter(place=place)
        context['communities'] = Community.get_actual().filter(place=place)
        context['events'] = Event.get_actual().filter(place=place)
        context['vacancies'] = Vacancy.get_actual().filter(place=place)
        context['stats_salary'] = Vacancy.get_salary_stats(place)


class PlaceListingView(RealmView):
    """Представление с картой и списком всех известных мест."""

    def get(self, request: HttpRequest) -> HttpResponse:
        places = Place.get_actual().order_by('-supporters_num', 'title')
        return self.render(request, {self.realm.name_plural: places})
