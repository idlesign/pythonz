from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from siteajax.toolbox import ajax_dispatch

from ..generics.views import DetailsView, RealmView, HttpRequest
from ..models import Place, User, Community, Event, Vacancy


class PlaceDetailsView(DetailsView):
    """Представление с детальной информацией о месте."""

    @method_decorator(login_required)
    def set_im_here(self, request: HttpRequest, obj_id: int) -> HttpResponse:
        """Обслуживает ajax-запрос. Прописывает место и часовой пояс в профиль пользователя.

        :param request:
        :param obj_id:

        """
        user = request.user
        user.place = self.get_object(request=request, obj_id=obj_id)
        user.set_timezone_from_place()
        user.save()

        return HttpResponse()

    @ajax_dispatch({
        'set-im-here': set_im_here
    })
    def get(self, request: HttpRequest, obj_id: int) -> HttpResponse:
        # Метод перекрыт для добавления AJAX-обработчика.
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
