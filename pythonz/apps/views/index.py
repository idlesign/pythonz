from itertools import groupby
from operator import attrgetter

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect

from ..generics.views import HttpRequest
from ..models import ExternalResource


@cache_page(900)  # 15 минут
@csrf_protect
def index(request: HttpRequest) -> HttpResponse:
    """Индексная страница."""
    from ..realms import get_realms

    realms_data = []
    realms_registry = get_realms()

    externals = ExternalResource.objects.filter(realm_name__in=realms_registry.keys())
    externals = {
        k: sorted(v, key=attrgetter('id'), reverse=True)
        for k, v in groupby(externals, attrgetter('realm_name'))}

    max_items = 6
    min_local = 2

    for name, realm in realms_registry.items():

        if not realm.show_on_main:
            continue

        realm_externals = externals.get(name, [])[:max_items]
        count_local = max_items - len(realm_externals)

        if count_local < min_local:
            count_local = min_local

        items = list(realm.model.get_actual()[:count_local])
        items.extend(realm_externals[:max_items - count_local])

        realms_data.append({
            'cls': realm,
            'items': items,
        })

    return render(request, 'index.html', {'realms_data': realms_data})
