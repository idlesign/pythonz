from textwrap import wrap
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlparse, urlencode, urlunparse

import os
import re
import requests
from PIL import Image  # Для работы с jpg требуется собрать с libjpeg-dev
from collections import OrderedDict
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.text import Truncator


def truncate_chars(text, to, html=False):
    """Укорачивает поданный на вход текст до опционально указанного количества символов."""
    return Truncator(text).chars(to, html=html)


def truncate_words(text, to, html=False):
    """Укорачивает поданный на вход текст до опционально указанного количества слов."""
    return Truncator(text).words(to, html=html)


def format_currency(val):
    """Форматирует значение валюты, разбивая его кратно
    тысяче для облегчения восприятия.

    :param val:
    :return:
    """
    return ' '.join(wrap(str(int(val))[::-1], 3))[::-1]


def update_url_qs(url, new_qs_params):
    """Дополняет указанный URL указанными параметрами запроса,
    при этом заменяя значения уже имеющихся одноимённых параметров, если
    таковые были в URL изначально

    :param str url:
    :param dict new_qs_params:
    :rtype: str
    """
    parsed = list(urlparse(url))
    parsed_qs = parse_qs(parsed[4])
    parsed_qs.update(new_qs_params)
    parsed[4] = urlencode(parsed_qs, doseq=True)
    return urlunparse(parsed)


class UTM:
    """Утилиты для работы с UTM (Urchin Tracking Module) метками."""

    @classmethod
    def add_to_url(cls, url, source, medium, campaign):
        """Добавляет UTM метки в указаный URL.

        :param url:

        :param source: Название источника перехода.
            Например, pythonz, google.

        :param medium: Рекламный канал.
            Например referral, cpc, banner, email

        :param campaign: Ключевое слово (название компании).
            Например слоган продукта, промокод.

        :rtype: str
        """
        params = {
            'utm_source': source,
            'utm_medium': medium,
            'utm_campaign': campaign,
        }
        return update_url_qs(url, params)

    @classmethod
    def add_to_external_url(cls, url):
        """Добавляет UTM метки в указанный внешний URL.

        :param str url:
        :rtype: str
        """
        return cls.add_to_url(url, 'pythonz', 'referral', 'item')

    @classmethod
    def add_to_internal_url(cls, url, source):
        """Добавляет UTM метки в указанный внутренний URL.

        :param str url:
        :param str source:
        :rtype: str
        """
        return cls.add_to_url(url, source, 'link', 'promo')


class BasicTypograph(object):
    """Содержит базовые правила типографики.
    Позволяет применить эти правила к строке.

    """

    rules = OrderedDict((
        ('QUOTES_REPLACE', (re.compile('(„|“|”|(\'\'))'), '"')),
        ('DASH_REPLACE', (re.compile('(-|­|–|—|―|−|--)'), '-')),

        ('SEQUENTIAL_SPACES', (re.compile('([ \t]+)'), ' ')),

        ('DASH_EM', (re.compile('([ ,])-[ ]'), '\g<1>— ')),
        ('DASH_EN', (re.compile('(\d+)[ ]*-[ ]*(\d+)'), '\g<1>–\g<2>')),

        ('HELLIP', (re.compile('\.{2,3}'), '…')),
        ('COPYRIGHT', (re.compile('\((c|с)\)'), '©')),
        ('TRADEMARK', (re.compile('\(tm\)'), '™')),
        ('TRADEMARK_R', (re.compile('\(r\)'), '®')),

        ('QUOTES_CYR_CLOSE', (re.compile('(\S+)"', re.U), '\g<1>»')),
        ('QUOTES_CYR_OPEN', (re.compile('"(\S+)', re.U), '«\g<1>')),
    ))

    @classmethod
    def apply_to(cls, input_str):
        input_str = ' %s ' % input_str.strip()

        for name, (regexp, replacement) in cls.rules.items():
            input_str = re.sub(regexp, replacement, input_str)

        return input_str.strip()


def url_mangle(url):
    """Усекает длинные URL практически до неузноваемости, делая нефункциональным, но коротким.
    Всё ради уменьшения длины строки.

    :param url:
    :return:
    """
    if len(url) <= 45:
        return url
    path, qs, frag = 2, 3, 4
    splitted = list(urlsplit(url))
    splitted[qs] = ''
    splitted[frag] = ''
    if splitted[path].strip('/'):
        splitted[path] = '<...>%s' % splitted[path].split('/')[-1]  # Последний кусок пути.
    mangled = urlunsplit(splitted)
    return mangled


def get_thumb_url(realm, image, width, height, absolute_url=False):
    """Создаёт на лету уменьшенную копию указанного изображения.

    :param realm:
    :param image:
    :param width:
    :param height:
    :param absolute_url:
    :return:
    """
    base_path = os.path.join('img', realm.name_plural, 'thumbs', '%sx%s' % (width, height))
    try:
        thumb_file_base = os.path.join(base_path, os.path.basename(image.path))
    except (ValueError, AttributeError):
        return ''

    cache_key = 'thumbs|%s|%s' % (thumb_file_base, absolute_url)

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
            url = '%s%s' % (settings.SITE_URL, url)

        cache.set(cache_key, url, 86400)

    return url


def get_timezone_name(lat, lng):
    """Возвращает имя часового пояса по геокоординатам, либо None.
    Использует Сервис Google Time Zone API.

    :param lat: широта
    :param lng: долгота
    :return:
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


def get_location_data(location_name):
    """Возвращает геоданные об объекте по его имени, либо None.
    Использует API Яндекс.Карт.

    :param location_name:
    :return:
    """

    url = 'http://geocode-maps.yandex.ru/1.x/?results=1&format=json&geocode=%s' % location_name
    try:
        result = requests.get(url)
        doc = result.json()
    except Exception:
        return None

    found = doc['response']['GeoObjectCollection']['metaDataProperty']['GeocoderResponseMetaData']['found']
    if not int(found):
        return None

    object_dict = doc['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
    object_bounds_dict = object_dict['boundedBy']['Envelope']
    object_metadata_dict = object_dict['metaDataProperty']['GeocoderMetaData']

    location_data = {
        'requested_name': location_name,
        'type': object_metadata_dict['kind'],
        'name': object_metadata_dict['text'],
        'country': object_metadata_dict['AddressDetails']['Country']['CountryName'],
        'pos': ','.join(reversed(object_dict['Point']['pos'].split(' '))),
        'bounds': '%s|%s' % (object_bounds_dict['lowerCorner'], object_bounds_dict['upperCorner']),
    }

    return location_data
