from urllib.parse import quote_plus

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from siteajax.decorators import ajax_dispatch
from siteajax.utils import AjaxResponse

from ..generics.views import HttpRequest
from ..models import Reference, ReferenceMissing, Category, Person, App
from ..utils import message_warning, search_models

def suggest(request):
    search_term, results = search_models(
        request.POST.get('text', ''), search_in=(
            Category,
            Person,
            Reference,
            App,
        ))
    if len(results) > 5:
        results = results[:5]
    return render(request, 'static/suggest_results.html', {'results': results})

@ajax_dispatch({
    'tags': suggest
})
def search(request: HttpRequest) -> HttpResponse:
    """Страница с результатами поиска по справочнику.
    Если найден один результат, перенаправляет на страницу результата.

    """
    search_term, results = search_models(
        request.POST.get('text', ''), search_in=(
            Category,
            Person,
            Reference,
            App,
        ))

    if not search_term:
        return redirect('index')

    if not results:
        # Поиск не дал результатов. Запомним, что искали и сообщим администраторам,
        # чтобы приняли меры по возможности.

        ReferenceMissing.add(search_term)

        message_warning(
            request, 'Поиск по справочнику и категориям не дал результатов, '
                     'и мы переключились на поиск по всему сайту.')

        # Перенаправляем на поиск по всему сайту.
        redirect_response = redirect('search_site')
        redirect_response['Location'] += f'?searchid={settings.YANDEX_SEARCH_ID}&text={quote_plus(search_term)}'

        return redirect_response

    results_len = len(results)

    if results_len == 1:
        return redirect(results[0].get_absolute_url())

    return render(request, 'static/search.html', {
        'search_term': search_term,
        'results': results,
        'results_len': results_len,
    })
