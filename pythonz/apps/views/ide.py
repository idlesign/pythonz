from django.http import HttpResponse
from django.shortcuts import render

from ..generics.views import HttpRequest
from ..models import Reference
from ..utils import search_models


def ide(request: HttpRequest) -> HttpResponse:
    """Страница подсказок для IDE."""

    term = request.GET.get('term', '')
    results = []
    error = ''

    ide_version = request.headers.get('Ide-Version')
    ide_name = request.headers.get('Ide-Name')

    if ide_version and ide_name:

        if ide_name in {'IntelliJ IDEA', 'PyCharm'}:
            term, results = search_models(term, search_in=(Reference,))

        else:
            error = f'Используемая вами среда разработки "{ide_name} {ide_version}" не поддерживается.'

    return render(request, 'realms/references/ide.html', {'term': term, 'results': results, 'error': error})
