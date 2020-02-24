import os
from typing import List, Optional

import requests
from PIL import Image
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils import timezone
from requests import Response

from ..signals import sig_integration_failed
from ..utils import truncate_words, truncate_chars

if False:  # pragma: nocover
    from ..generics.realms import RealmBase


def get_from_url(url: str, *, method: str = 'get', **kwargs) -> Response:
    """Возвращает объект ответа requests с указанного URL.
    
    По умолчанию запрос производится методом GET.
    
    :param url:
    :param method: get, post

    """
    r_kwargs = {
        'allow_redirects': True,
        'headers': {'User-agent': settings.USER_AGENT},
    }
    r_kwargs.update(kwargs)

    method = getattr(requests, method)

    return method(url, **r_kwargs)


def get_json(url: str, return_none_statuses: List[int] = None) -> dict:
    """Возвращает словарь, созданный из JSON документа, полученного
    с указанного URL.

    :param url:
    :param list return_none_statuses: Коды статусов, для которых требуется вернуть None.

    """
    return_none_statuses = return_none_statuses or []
    result = {}

    try:
        response = get_from_url(url)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:

        status = getattr(e.response, 'status_code', 0)

        if status in return_none_statuses:
            return {}

        elif status != 503:
            # Temporary Unavailable. В следующий раз получится.
            sig_integration_failed.send(None, description=f'URL {url}. Error: {e}')

    else:

        try:
            result = response.json()

        except ValueError:
            pass

    return result


def get_image_from_url(url: str) -> ContentFile:
    """Забирает изображение с указанного URL.

    :param url:

    """
    return ContentFile(requests.get(url).content, url.rsplit('/', 1)[-1])


def scrape_page(url: str) -> dict:
    """Возвращает словарь с данными о странице, либо None в случае ошибок.

    Словарь вида:
        {'title': '...', 'content_more': '...', 'content_less': '...', ...}

    :param url:

    """
    # Функция использовала ныне недоступный Rich Content API от Яндекса для получения данных о странице.
    # Если функциональность будет востребована, нужно будет перевести на использование догого механизма.
    result = {}

    if 'content' not in result:
        return {}

    content = result['content']
    result['content_less'] = truncate_words(content, 30)
    result['content_more'] = truncate_chars(content, 900).replace('\n', '\n\n')

    return result


def make_soup(page: str) -> BeautifulSoup:
    """Возвращает объект BeautifulSoup, либо None для указанного URL.

    :param page:

    """
    return BeautifulSoup(page, 'lxml')


def get_thumb_url(realm: 'RealmBase', image: Image, width: int, height: int, absolute_url: bool = False) -> str:
    """Создаёт на лету уменьшенную копию указанного изображения.

    :param realm:
    :param image:
    :param width:
    :param height:
    :param absolute_url:

    """
    base_path = os.path.join('img', realm.name_plural, 'thumbs', f'{width}x{height}')

    try:
        thumb_file_base = os.path.join(base_path, os.path.basename(image.path))

    except (ValueError, AttributeError):
        return ''

    cache_key = f'thumbs|{thumb_file_base}|{absolute_url}'

    url = cache.get(cache_key)

    if url is None:

        thumb_file = os.path.join(settings.MEDIA_ROOT, thumb_file_base)

        if not os.path.exists(thumb_file):

            try:
                os.makedirs(os.path.join(settings.MEDIA_ROOT, base_path), mode=0o755)

            except FileExistsError:
                pass

            img = Image.open(image)
            img.thumbnail((width, height), Image.ANTIALIAS)
            img.convert('RGB').save(thumb_file)

        url = os.path.join(settings.MEDIA_URL, thumb_file_base)

        if absolute_url:
            url = f'{settings.SITE_URL}{url}'

        cache.set(cache_key, url, 86400)

    return url


def get_timezone_name(lat: str, lng: str) -> Optional[str]:
    """Возвращает имя часового пояса по геокоординатам, либо None.
    Использует Сервис Google Time Zone API.

    :param lat: широта
    :param lng: долгота

    """
    url = (
        'https://maps.googleapis.com/maps/api/timezone/json?'
        'location=%(lat)s,%(lng)s&timestamp=%(ts)s&key=%(api_key)s' % {
            'lat': lat,
            'lng': lng,
            'ts': timezone.now().timestamp(),
            'api_key': settings.GOOGLE_API_KEY,
        }
    )

    try:
        result = requests.get(url)
        doc = result.json()
        tz_name = doc['timeZoneId']

    except Exception:
        return None

    return tz_name


def get_location_data(location_name: str) -> dict:
    """Возвращает геоданные об объекте по его имени, либо None.
    Использует API Яндекс.Карт.

    :param location_name:

    """
    url = 'https://geocode-maps.yandex.ru/1.x/'

    try:
        result = requests.get(url, params={
            'results': 1,
            'format': 'json',
            'geocode': location_name,
            'apikey': settings.YANDEX_GEOCODER_KEY,
        })
        doc = result.json()

    except Exception:
        return {}

    response = doc.get('response')
    if not response:
        return {}

    collection = response['GeoObjectCollection']
    found = collection['metaDataProperty']['GeocoderResponseMetaData']['found']

    if not int(found):
        return {}

    object_dict = collection['featureMember'][0]['GeoObject']
    object_bounds_dict = object_dict['boundedBy']['Envelope']
    object_metadata_dict = object_dict['metaDataProperty']['GeocoderMetaData']

    location_data = {
        'requested_name': location_name,
        'type': object_metadata_dict['kind'],
        'name': object_metadata_dict['text'],
        'country': object_metadata_dict['AddressDetails']['Country']['CountryName'],
        'pos': ','.join(reversed(object_dict['Point']['pos'].split(' '))),
        'bounds': f"{object_bounds_dict['lowerCorner']}|{object_bounds_dict['upperCorner']}",
    }

    return location_data
