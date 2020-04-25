from django.shortcuts import get_object_or_404
from django.urls import reverse
from sitecats.toolbox import get_category_lists, get_category_aliases_under

from ..generics.views import RealmView, HttpRequest
from ..models import Category


class CategoryListingView(RealmView):
    """Выводит список известных категорий, либо список сущностей для конкретной категории."""

    def get(self, request: HttpRequest, obj_id: int = None):
        from ..realms import get_realms

        realms = get_realms().values()

        if obj_id is None:  # Запрошен список всех известных категорий.
            item = get_category_lists(
                init_kwargs={
                    'show_title': True,
                    'show_links': lambda cat: reverse(self.realm.get_details_urlname(), args=[cat.id])
                },
                additional_parents_aliases=get_category_aliases_under())

            return self.render(request, {'item': item, 'realms': realms})

        # Выводим список материалов (разбитых по областям сайта) для конкретной категории.
        category = get_object_or_404(Category.objects.select_related('parent'), pk=obj_id)

        realms_links = {}

        for realm in realms:
            realm_model = realm.model

            if not hasattr(realm_model, 'categories'):  # ModelWithCategory
                continue

            items = realm_model.get_objects_in_category(category)

            if not items:
                continue

            realm_title = realm_model.get_verbose_name_plural()

            _, plural = realm.get_names()

            realms_links[realm_title] = (plural, items)

        return self.render(request, {self.realm.name: category, 'item': category, 'realms_links': realms_links})
