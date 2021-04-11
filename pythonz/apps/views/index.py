from datetime import timedelta
from itertools import groupby
from operator import attrgetter
from typing import List

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.timezone import now
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect

from ..generics.models import RealmBaseModel
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

    dt_stale_featured = now() - timedelta(days=7)
    """Дата, начиная с которой следует считать материал устаревшим."""

    for name, realm in realms_registry.items():

        if not realm.show_on_main:
            continue

        realm_externals = externals.get(name, [])[:max_items]
        count_local = max_items - len(realm_externals)

        if count_local < min_local:
            count_local = min_local

        actual = realm.model.get_actual()
        items: List[RealmBaseModel] = list(actual[:count_local])
        items.extend(realm_externals[:max_items - count_local])

        featured = None
        if items:
            featured = items[0]
            if (featured.time_modified or featured.time_created) < dt_stale_featured:
                # Объект устарел, покажем что-нибудь случайное.
                # ? ведёт себя сносно, пока таблица влезает в память.
                featured = actual.filter(id__lt=featured.id).order_by('?').first() or featured

        realms_data.append({
            'featured': featured,
            'cls': realm,
            'items': items,
        })

    return render(request, 'index.html', {'realms_data': realms_data})
