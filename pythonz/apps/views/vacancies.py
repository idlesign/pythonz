
from ..generics.views import HttpRequest, ListingView
from ..models import Vacancy


class VacancyListingView(ListingView):
    """Представление со списком вакансий."""

    def update_context(self, context: dict, request: HttpRequest):
        context['stats_salary'] = Vacancy.get_salary_stats()
        context['stats_places'] = Vacancy.get_places_stats()

    def get_most_voted_objects(self) -> list:
        return []
