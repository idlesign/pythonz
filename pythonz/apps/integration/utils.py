import os
from collections import namedtuple
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional, Set, Callable, Dict, Union

import requests
from PIL import Image, UnidentifiedImageError
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db.models.fields.files import ImageFieldFile
from django.utils import timezone
from requests import Response

from ..signals import sig_integration_failed
from ..utils import truncate_words, truncate_chars

if False:  # pragma: nocover
    from ..generics.realms import RealmBase  # noqa


PageInfo = namedtuple('PageInfo', ['title', 'description', 'site_name', 'images'])


def get_page_info(url: str, timeout: int = 4) -> Optional[PageInfo]:
    """Возвращает информацию о странице, расположенной
    по указанному адресу, либо None.

    :param url:
    :param timeout: Таймаут на подключение.

    """
    return None


def get_from_url(url: str, *, method: str = 'get', **kwargs) -> Response:
    """Возвращает объект ответа requests с указанного URL.
    
    По умолчанию запрос производится методом GET.
    
    :param url:
    :param method: get, post

    """
    r_kwargs = {
        'allow_redirects': True,
        'headers': {'User-agent': settings.USER_AGENT},
        'timeout': 15,
    }
    r_kwargs.update(kwargs)

    method = getattr(requests, method)

    return method(url, **r_kwargs)


def get_json(url: str, *, return_none_statuses: Set[int] = None, silent_statuses: Set[int] = None) -> dict:
    """Возвращает словарь, созданный из JSON документа, полученного
    с указанного URL.

    :param url:
    :param return_none_statuses: Коды статусов, для которых требуется вернуть None.
    :param silent_statuses: Коды статусов, для которых не требуется рассылать оповещения об ошибках.

    """
    return_none_statuses = return_none_statuses or set()
    result = {}

    try:
        response = get_from_url(url)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:

        status = getattr(e.response, 'status_code', 0)

        if status in return_none_statuses:
            return {}

        elif status != 503 and status not in silent_statuses:
            # Temporary Unavailable. В следующий раз получится.
            sig_integration_failed.send(None, description=f'URL {url}.\nError: {e}')

    else:

        try:
            result = response.json()

        except ValueError:
            pass

    return result


def get_image_from_url(url: str) -> Optional[ContentFile]:
    """Забирает изображение с указанного URL.

    :param url:

    """
    response = requests.get(url)
    content = response.content

    if response.status_code != 200 or not content:
        return None

    return ContentFile(content, url.rstrip('/').rsplit('/', 1)[-1])


def scrape_page(url: str) -> dict:
    """Возвращает словарь с данными о странице, либо None в случае ошибок.

    Словарь вида:
        {'title': '...', 'content_more': '...', 'content_less': '...', ...}

    :param url:

    """
    # Функция использовала ныне недоступный Rich Content API от Яндекса для получения данных о странице.
    # Если функциональность будет востребована, нужно будет перевести на использование догого механизма.
    result = {}

    # todo Быть может перейти на get_page_info().

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


def get_thumb_url(
        realm: 'RealmBase',
        image: ImageFieldFile,
        width: int,
        height: int,
        absolute_url: bool = False
) -> str:
    """Создаёт на лету уменьшенную копию указанного изображения.

    :param realm:
    :param image:
    :param width:
    :param height:
    :param absolute_url:

    """
    base_path = Path('img') / realm.name_plural / 'thumbs' / f'{width}x{height}'

    try:
        thumb_file_base = base_path / Path(image.path).name

    except (ValueError, AttributeError):
        return ''

    cache_key = f'thumbs|{thumb_file_base}|{absolute_url}'

    url = cache.get(cache_key)

    if url is None:

        thumb_file = Path(settings.MEDIA_ROOT) / thumb_file_base

        if not thumb_file.exists():

            try:
                os.makedirs(os.path.join(settings.MEDIA_ROOT, base_path), mode=0o755)

            except FileExistsError:
                pass

            try:
                img = Image.open(image)

            except UnidentifiedImageError:
                # сбойное изображение
                image.delete()
                return ''

            else:
                img.thumbnail((width, height), Image.ANTIALIAS)
                img.convert('RGB').save(f'{thumb_file}', format=img.format.lower())

        url = Path(settings.MEDIA_URL) / thumb_file_base
        url = f'{url}'

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


def run_threads(items: Union[List, Set], func: Callable, *, thread_num: int = None) -> Dict[str, Optional[PageInfo]]:
    """Возвращает результаты обработки в нитях указанной функцей указанных элементов.

    :param items: Элементы для обработки.

    :param func: Функция для вызова.

    :param thread_num: Количество нитей для забора данных.
        Если не указано, о будет создано нитей по количеству элементов,
        но не более определённого числа.

    """
    result = {}

    if not thread_num:
        max_auto_threads = 12

        thread_num = len(items)

        if thread_num > max_auto_threads:
            thread_num = max_auto_threads

    if not thread_num:
        return result

    with ThreadPoolExecutor(max_workers=thread_num) as executor:

        task_to_item = {
            executor.submit(func, item): item
            for item in items}

        for task in as_completed(task_to_item):
            item = task_to_item[task]
            result[item] = task.result()

    return result
