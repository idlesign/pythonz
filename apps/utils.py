import re
from collections import  OrderedDict
from urllib.parse import urlsplit, urlunsplit
from datetime import timedelta

import requests
from sitemessage.toolbox import schedule_messages, recipients
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import Truncator
from django.utils import timezone

from .sitemessages import PythonzTwitterMessage, PythonzEmailNewEntity, PythonzEmailDigest


PROJECT_SOURCE_URL = 'https://github.com/idlesign/pythonz'


class BasicTypograph(object):
    """Содержит базовые правила типографики.
    Позволяет применить эти правила к строке.

    """

    rules = OrderedDict((
        ('QUOTES_REPLACE', (re.compile('(„|“|”|(\'\'))', re.M | re.U), '"')),
        ('DASH_REPLACE', (re.compile('(-|­|–|—|―|−|--)', re.M | re.U), '-')),

        ('SEQUENTIAL_SPACES', (re.compile('(\s+|\t+)', re.M | re.U), ' ')),

        ('DASH_EM', (re.compile('(\s|,)-\s', re.M | re.U), '\g<1>— ')),
        ('DASH_EN', (re.compile('(\d+)\s*-\s*(\d+)', re.M | re.U), '\g<1>–\g<2>')),

        ('HELLIP', (re.compile('\.{2,3}', re.M | re.U), '…')),
        ('COPYRIGHT', (re.compile('\((c|с)\)', re.M | re.U), '©')),
        ('TRADEMARK', (re.compile('\(tm\)', re.M | re.U), '™')),
        ('TRADEMARK_R', (re.compile('\(r\)', re.M | re.U), '®')),

        ('QUOTES_CYR_CLOSE', (re.compile('(\S+)"', re.M | re.U), '\g<1>»')),
        ('QUOTES_CYR_OPEN', (re.compile('"(\S+)', re.M | re.U), '«\g<1>')),
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


def create_digest():
    """Создаёт депеши для рассылки еженедельного дайджеста.

    Реальная компиляция дайджеста происходит в PythonzEmailDigest.compile().

    :return:
    """
    if settings.DEBUG:  # На всякий случай, чем чёрт не шутит.
        return False
    from .models import User
    date_till = timezone.now()
    date_from = date_till-timedelta(days=7)
    context = {'date_from': date_from.timestamp(), 'date_till': date_till.timestamp()}
    format_date = lambda d: d.date().strftime('%d.%m.%Y')
    m = PythonzEmailDigest(get_email_full_subject('Подборка материалов %s-%s' % (format_date(date_from), format_date(date_till))), context)
    subscribers = User.get_digest_subsribers()
    schedule_messages(m, recipients('smtp', subscribers))


def get_admins_emails():
    """Возвращает адреса электронной почты администраторов проекта.

    :return:
    """
    to = []
    for item in settings.ADMINS:
        to.append(item[1])  # Адрес электронной почты админа.
    return to


def get_email_full_subject(subject):
    """Возвращает полный заголовок для электронного письма.

    :param subject:
    :return:
    """
    return 'pythonz.net: %s' % subject


def notify_entity_published(entity):
    """Отсылает оповещение о публикации сущности.

    :param RealmBaseModel entity:
    :return:
    """
    MAX_LEN = 139  # Максимальная длина тивта. Для верности меньше.
    prefix = 'Новое: %s «' % entity.get_verbose_name()
    url = 'http://pythonz.net%s' % entity.get_absolute_url()
    postfix = '» %s' % url
    if settings.AGRESSIVE_MODE:
        postfix = '%s #python #dev' % postfix
    title = Truncator(entity.title).chars(MAX_LEN - len(prefix) - len(postfix))
    message = '%s%s%s' % (prefix, title, postfix)
    schedule_messages(PythonzTwitterMessage(message), recipients('twitter', ''))


def notify_new_entity(entity):
    """Отсылает оповещение о создании новой сущности.

    Рассылается администраторам проекта.

    :param RealmBaseModel entity:
    :return:
    """
    context = {
        'entity_title': entity.title,
        'entity_url': entity.get_absolute_url()
    }
    m = PythonzEmailNewEntity(get_email_full_subject('Добавлена новая сущность - %s' % entity.title), context)
    schedule_messages(m, recipients('smtp', get_admins_emails()))


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
    url = 'https://maps.googleapis.com/maps/api/timezone/json?location=%(lat)s,%(lng)s&timestamp=%(ts)s&key=%(api_key)s' % {
        'lat': lat,
        'lng': lng,
        'ts': timezone.now().timestamp(),
        'api_key': settings.GOOGLE_API_KEY,
    }
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
