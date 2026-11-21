from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from ..generics.views import HttpRequest
from ..models import ReferenceMissing
from ..search import find_exact, search_areas

SUGGEST_LIMIT: int = 6
"""Максимальное число вариантов в поисковой подсказке."""


def search(request: HttpRequest) -> HttpResponse:
    """Единая страница поиска по сайту.

    При точном совпадении запроса с категорией или персоной перенаправляет
    на страницу объекта, равно как и при единственном найденном результате.

    """
    results = search_areas(request.POST.get('text', ''))

    if not results.term:
        return redirect('index')

    if exact := find_exact(results.term):
        return redirect(exact.get_absolute_url())

    total = results.total

    if not total:
        # Поиск не дал результатов. Запомним, что искали и сообщим администраторам,
        # чтобы приняли меры по возможности.
        ReferenceMissing.add(results.term)

    if total == 1:
        return redirect(results.groups[0].results[0].get_absolute_url())

    return render(request, 'static/search.html', {
        'search_term': results.term,
        'groups': results.groups,
        'results_len': total,
    })


def search_suggest(request: HttpRequest) -> JsonResponse:
    """Обслуживает ajax-запрос. Подсказывает наиболее релевантные результаты поиска."""
    results = []

    if len(term := request.GET.get('q', '').strip()) >= 2:

        for group in search_areas(term).groups:
            results.extend({
                'value': obj.get_absolute_url(),
                'text': obj.title,
                'area': group.area.title,
            } for obj in group.results)

    return JsonResponse({'results': results[:SUGGEST_LIMIT]})
