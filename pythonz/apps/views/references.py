from django.http import HttpResponse
from django.shortcuts import redirect

from ..generics.views import DetailsView, HttpRequest, RealmView
from ..models import Reference

TREE_PREFIX_MIN_ITEMS: int = 3
"""Минимальное число статей с общим префиксом названия, при котором
префикс убирается из названий в дереве близлежащих разделов."""


def shorten_tree_titles(items: list[Reference]) -> list[Reference]:
    """Сокращает названия статей для компактного отображения в дереве.

    Если названия нескольких статей начинаются с общего префикса
    (например «object.»), префикс убирается из этих названий.
    Сокращённое название записывается в атрибут `title_short`.

    :param items: Статьи справочника.

    """
    prefix_counts = {}

    for item in items:

        title = item.title
        start = 0

        while (pos := title.find('.', start)) != -1 and pos < len(title) - 1:
            prefix = title[:pos + 1]
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
            start = pos + 1

    prefixes = {prefix for prefix, count in prefix_counts.items() if count >= TREE_PREFIX_MIN_ITEMS}

    for item in items:

        title = item.title
        strip_len = 0
        start = 0

        while (pos := title.find('.', start)) != -1 and pos < len(title) - 1:
            if title[:pos + 1] in prefixes:
                strip_len = pos + 1
            start = pos + 1

        item.title_short = title[strip_len:]

    return items


class ReferenceListingView(RealmView):
    """Представление со списком справочников."""

    def get(self, request: HttpRequest) -> HttpResponse:
        # Справочник один, поэтому перенаправляем сразу на него.
        return redirect(self.realm.get_details_urlname(slugged=True), 'python', permanent=True)


class ReferenceDetailsView(DetailsView):
    """Представление статьи справочника."""

    def update_context(self, context: dict, request: HttpRequest):

        reference = context['item']
        children = shorten_tree_titles(list(reference.get_actual(
            parent=reference).order_by('title').select_related('version_deprecated')))

        context['children'] = children
        context['children_grouped'] = reference.group_by_type(children)

        if reference.parent is not None:
            # Текущая статья включается в список соседних для отображения дерева раздела.
            siblings = list(reference.get_actual(
                parent=reference.parent).order_by('title').select_related('version_deprecated'))
            context['siblings'] = shorten_tree_titles(siblings)
