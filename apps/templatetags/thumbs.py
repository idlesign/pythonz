from django import template

from ..utils import get_thumb_url


register = template.Library()


@register.simple_tag(takes_context=True)
def thumbs_get_thumb_url(context, image, width, height, realm, as_=None, as_name=None):
    """Создаёт на лету уменьшенную копию указанного изображения.

    :param context:
    :param image:
    :param width:
    :param height:
    :param realm:
    :param as_:
    :param as_name:
    :return:
    """
    url = get_thumb_url(realm, image, width, height)
    if as_name is not None:
        context[as_name] = url
        return ''
    return url
