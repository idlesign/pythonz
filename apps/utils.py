import requests

from django.core.files.base import ContentFile


PROJECT_SOURCE_URL = 'https://github.com/idlesign/pythonz'


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
