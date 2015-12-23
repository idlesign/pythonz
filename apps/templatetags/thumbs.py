from django import template

from ..utils import get_thumb_url


register = template.Library()


@register.simple_tag(takes_context=True)
def thumbs_get_thumb_url(context, image, width, height, realm):
    """Создаёт на лету уменьшенную копию указанного изображения.

    :param context:
    :param image:
    :param width:
    :param height:
    :param realm:
    :return:
    """
    return get_thumb_url(realm, image, width, height)
