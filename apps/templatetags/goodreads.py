from urllib.parse import urlencode

from django import template


register = template.Library()

@register.simple_tag
def goodreads_get_search_tag(query):
    """Возврщает тег ссылки на поиск ISBN по сайту Goodreads.

    :param query:
    :return:
    """
    url = 'https://www.goodreads.com/search/?%s' % urlencode({'query': query})
    return '<a href="%s" title="Искать на goodreads.com"><span class="glyphicon glyphicon-search"></span></a>' % url
