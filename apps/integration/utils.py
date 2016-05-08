import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile

from pythonz import VERSION
from ..signals import sig_integration_failed
from ..utils import truncate_words, truncate_chars


USER_AGENT = 'pythonz.net/%s (press@pythonz.net)' % '.'.join(map(str, VERSION))


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

        if getattr(e.response, 'status_code', 0) != 503:  # Temporary Unavailable. В следующий раз получится.
            sig_integration_failed.send(None, description='URL %s. Error: %s' % (url, e))

    else:
        try:
            result = response.json()
        except ValueError:
            pass

    return result


def get_image_from_url(url):
    """Забирает изображение с указанного URL.

    :param url:
    :return:
    """
    return ContentFile(requests.get(url).content, url.rsplit('/', 1)[-1])


def scrape_page(url):
    """Возвращает словарь с данными о странице, либо None в случае ошибок.

    Словарь вида:
        {'title': '...', 'content_more': '...', 'content_less': '...', ...}

    :param url:
    :return:
    """

    # Функция использовала ныне недоступный Rich Content API от Яндекса для получения данных о странице.
    # Если функциональность будет востребована, нужно будет перевести на использование догого механизма.
    result = {}

    if 'content' not in result:
        return None

    content = result['content']
    result['content_less'] = truncate_words(content, 30)
    result['content_more'] = truncate_chars(content, 900).replace('\n', '\n\n')

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
        result = BeautifulSoup(response.text, 'html5lib')
    except requests.exceptions.RequestException:
        pass

    return result