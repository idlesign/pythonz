from urllib.parse import urlencode

from django import template
from django.template.defaultfilters import safe

register = template.Library()


@register.simple_tag
def goodreads_get_search_tag(query: str):
    """Возврщает тег ссылки на поиск ISBN по сайту Goodreads.

    :param query:

    """
    url = f"https://www.goodreads.com/search/?{urlencode({'query': query})}"
    return safe(f'<a href="{url}" title="ISBN на goodreads.com">{query}</a>')
