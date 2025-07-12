
from django import template
from django.db.models.fields.files import ImageFieldFile

from ..generics.realms import RealmBase
from ..integration.utils import get_thumb_url

register = template.Library()


@register.simple_tag(takes_context=True)
def thumbs_get_thumb_url(
        context,
        image: str | ImageFieldFile,
        width: int,
        height: int,
        realm: RealmBase
) -> str:
    """Создаёт налету уменьшенную копию указанного изображения.

    :param context:
    :param image:
    :param width:
    :param height:
    :param realm:

    """
    if isinstance(image, str):
        url = image

    else:
        url = get_thumb_url(realm, image, width, height)

    return url
