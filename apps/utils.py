import os
import re
from collections import OrderedDict
from urllib.parse import urlsplit, urlunsplit
from textwrap import wrap


import requests
from PIL import Image  # Для работы с jpg требуется собрать с libjpeg-dev
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import Truncator

from pythonz import VERSION
from .signals import sig_integration_failed


USER_AGENT = 'pythonz.net/%s (press@pythonz.net)' % '.'.join(map(str, VERSION))


def format_currency(val):
    """Форматирует значение валюты, разбивая его кратно
    тысяче для облегчения восприятия.

    :param val:
    :return:
    """
    return ' '.join(wrap(str(int(val))[::-1], 3))[::-1]


def get_from_url(url):
    """Возвращает объект ответа requests с указанного URL.

    :param str url:
    :return:
    """
    r_kwargs = {
        'allow_redirects': True,
        'headers': {'User-agent': USER_AGENT},
    }
    return requests.get(url, **r_kwargs)


def get_json(url):
    """Возвращает словарь, созданный из JSON документа, полученного
    с указанного URL.

    :param str url:
    :return:
    """

    result = {}
    try:
        response = get_from_url(url)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        sig_integration_failed.send(None, description='URL %s. Error: %s' % (url, e))

    else:
        try:
            result = response.json()
        except ValueError:
            pass

    return result


class HhVacancyManager:
    """Объединяет инструменты для работы с вакансиями с hh.ru."""

    @classmethod
    def get_status(cls, url):
        """Возвращает состояние вакансии по указанному URL.

        :param url:
        :return:
        """
        response = get_json(url)
        if not response:
            return

        return response['archived']

    @classmethod
    def fetch_list(cls):
        """Возвращает словарь с данными вакансий, полученный из внешнего
        источника.

        :return:
        """
        base_url = 'https://api.hh.ru/vacancies/'
        query = (
            'search_field=%(field)s&per_page=%(per_page)s'
            '&order_by=publication_time&period=1&text=%(term)s' % {
                'term': 'python',
                'per_page': 500,
                'field': 'name',  # description
        })

        response = get_json('%s?%s' % (base_url, query))

        if 'items' not in response:
            return None

        results = []
        for item in response['items']:
            salary_from = salary_till = salary_currency = ''

            if item['salary']:
                salary = item['salary']
                salary_from = salary['from']
                salary_till = salary['to']
                salary_currency = salary['currency']

            employer = item['employer']
            url_logo = employer['logo_urls']
            if url_logo:
                url_logo = url_logo['90']

            results.append({
                '__archived': item['archived'],
                'src_id': item['id'],
                'src_place_name': item['area']['name'],
                'src_place_id': item['area']['id'],
                'title': item['name'],
                'url_site': item['alternate_url'],
                'url_api': item['url'],
                'url_logo': url_logo,
                'employer_name': employer['name'],
                'salary_from': salary_from or None,
                'salary_till': salary_till or None,
                'salary_currency': salary_currency,
                'time_published': parse_datetime(item['published_at']),
            })

        return results


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


def get_image_from_url(url):
    """Забирает изображение с указанного URL.

    :param url:
    :return:
    """
    return ContentFile(requests.get(url).content, url.rsplit('/', 1)[-1])


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


def scrape_page(url):
    """Возвращает словарь с данными о странице (полученными при помощи
    Rich Content API от Яндекса), либо None в случае ошибок.

    Словарь вида:
        {'title': '...', 'content_more': '...', 'content_less': '...', ...}

    :param url:
    :return:
    """

    url = 'http://rca.yandex.com/?key=%(api_key)s&url=%(url)s&content=full' % {
        'api_key': settings.YANDEX_RCA_KEY, 'url': url
    }

    result = get_json(url)

    if 'content' not in result:
        return None

    content = result['content']
    result['content_less'] = Truncator(content).words(30)
    result['content_more'] = Truncator(content).chars(900).replace('\n', '\n\n')

    return result


def make_soup(url):
    """Возвращает объект BeautifulSoup, либо None для указанного URL.

    :param str url:
    :return: object
    :rtype: BeautifulSoup|None
    """
    result = None
    try:
        response = get_from_url(url)
        result = BeautifulSoup(response.text)
    except requests.exceptions.RequestException:
        pass

    return result
