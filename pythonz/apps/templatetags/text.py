import re

from django import template
from django.template.defaultfilters import safe

register = template.Library()


RE_HREF = re.compile(r'href="([^"]+)"')


@register.filter
def nolinks(value: str):
    """Убирает из html гиперссылки.

    :param value:

    """
    return safe(f"{RE_HREF.sub('', value)}")
