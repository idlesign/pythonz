import requests
from datetime import timedelta

from sitemessage.toolbox import schedule_messages, recipients
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import Truncator
from django.utils import timezone

from .sitemessages import PythonzTwitterMessage, PythonzEmailNewEntity, PythonzEmailDigest


PROJECT_SOURCE_URL = 'https://github.com/idlesign/pythonz'


def create_digest():
    """Создаёт депеши для рассылки еженедельного дайджеста.

    Реальная компиляция дайджеста происходит в PythonzEmailDigest.compile().

    :return:
    """
    from .models import User
    date_till = timezone.now()
    date_from = date_till-timedelta(days=7)
    context = {'date_from': date_from.timestamp(), 'date_till': date_till.timestamp()}
    format_date = lambda d: d.date().strftime('%d.%m.%Y')
    m = PythonzEmailDigest(get_email_full_subject('Дайджест %s-%s' % (format_date(date_from), format_date(date_till))), context)
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
    postfix = '» %s' % entity.get_absolute_url()
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


def get_location_data(location_name):
    """Возвращает геоданные об объекте по его имени, используя API Яндекс.Карт.

    :param location_name:
    :return:
    """

    result = requests.get('http://geocode-maps.yandex.ru/1.x/?results=1&format=json&geocode=%s' % location_name)

    doc = result.json()

    object_dict = doc['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
    object_bounds_dict = object_dict['boundedBy']['Envelope']
    object_metadata_dict = object_dict['metaDataProperty']['GeocoderMetaData']

    location_data = {
        'type': object_metadata_dict['kind'],
        'name': object_metadata_dict['text'],
        'country': object_metadata_dict['AddressDetails']['Country']['CountryName'],
        'pos': object_dict['Point']['pos'],
        'bounds': '%s|%s' % (object_bounds_dict['lowerCorner'], object_bounds_dict['upperCorner']),
    }

    return location_data
