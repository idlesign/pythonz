from enum import Enum
from sys import maxsize
from typing import Type, Dict

from django.db.models import QuerySet

from ..generics.views import ListingView, HttpRequest
from ..models import PEP


class PepListingView(ListingView):
    """Представление со списком PEP."""

    def get_paginator_per_page(self, request: HttpRequest) -> int:
        if request.disable_paginator:
            return maxsize
        return super().get_paginator_per_page(request)

    def apply_object_filter(self, *, attrs: Dict[str, Type[Enum]], objects: QuerySet):

        applied = False

        for attr, enum in attrs.items():
            val = self.request.GET.get(attr)

            if val and val.isdigit():

                val = int(val)

                if val in enum.values:
                    objects = objects.filter(**{attr: val})
                    applied = True

        return applied, objects

    def get_paginator_objects(self) -> QuerySet:

        objects = super().get_paginator_objects()

        applied, objects = self.apply_object_filter(attrs={
            'status': PEP.Status,
            'type': PEP.Type,
        }, objects=objects)

        self.request.disable_paginator = applied

        return objects
