from itertools import groupby
from operator import attrgetter

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect

from ..generics.views import HttpRequest
from ..models import ExternalResource


@cache_page(1800)  # 30 минут
@csrf_protect
def index(request: HttpRequest) -> HttpResponse:
    """Индексная страница."""
    from ..realms import get_realms

    realms_data = []
    realms_registry = get_realms()

    externals = ExternalResource.objects.filter(realm_name__in=realms_registry.keys())
    externals = {k: list(v) for k, v in groupby(externals, attrgetter('realm_name'))}

    max_additional = 5

    for name, realm in realms_registry.items():

        if not realm.show_on_main:
            continue

        realm_externals = externals.get(name, [])
        count_externals = len(realm_externals)

        count_locals = 1
        if count_externals < max_additional:
            count_locals += max_additional - count_externals

        realm_locals = realm.model.get_actual()[:count_locals]

        if realm_locals:
            main = realm_locals[0]
            additional = list(realm_locals[1:]) + realm_externals[:max_additional]

        else:
            main = {}
            additional = []

        realms_data.append({
            'cls': realm,
            'main': main,
            'additional': additional,
        })

    return render(request, 'index.html', {'realms_data': realms_data})
