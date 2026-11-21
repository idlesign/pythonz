from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def staticv(path: str) -> str:
    """Возвращает URL статического файла, дополненный версией (н.п. /static/js/some.js?v=123).

    В качестве версии используется STATIC_VERSION из настроек (время запуска процесса),
    что позволяет не заботиться о ручном обновлении параметра ?v= для сброса кеша.

    :param path: Путь до файла относительно каталога со статикой.

    """
    return f'{static(path)}?v={settings.STATIC_VERSION}'
