from urllib.parse import urlencode

from django import template
from django.template.defaultfilters import safe

register = template.Library()


@register.simple_tag
def goodreads_get_search_tag(query):
    """Возврщает тег ссылки на поиск ISBN по сайту Goodreads.

    :param query:
    :return:
    """
    url = 'https://www.goodreads.com/search/?%s' % urlencode({'query': query})
    return safe('<a href="%s" title="ISBN на goodreads.com">%s</a>' % (url, query))
