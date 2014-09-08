import os

from django.conf import settings
from django import template

from PIL import Image  # Для работы с jpg требуется собрать с libjpeg-dev


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
    def get_result(url):
        if as_name is not None:
            context[as_name] = url
            return ''
        return url

    base_path = os.path.join('img', realm.name_plural, 'thumbs', '%sx%s' % (width, height))
    try:
        thumb_file_base = os.path.join(base_path, os.path.basename(image.path))
    except ValueError:
        return get_result('')
    thumb_file = os.path.join(settings.MEDIA_ROOT, thumb_file_base)

    if not os.path.exists(thumb_file):  # TODO Довольно долго. Пересмотреть при случае.
        try:
            os.makedirs(os.path.join(settings.MEDIA_ROOT, base_path), mode=0o755)
        except FileExistsError:
            pass
        img = Image.open(image)
        img.thumbnail((width, height), Image.ANTIALIAS)
        img.save(thumb_file)

    return get_result(os.path.join(settings.MEDIA_URL, thumb_file_base))
