from collections import OrderedDict
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.db.models import signals
from django.utils.timezone import now

from .utils import make_soup, get_from_url

_PARTNERS_REGISTRY = None
_CACHE_TIMEOUT = 28800  # 8 часов


class PartnerBase():
    """Базовый класс для работы с партнёрскими сайтами."""

    ident = None
    title = None
    link_mutator = None

    def __init__(self, partner_id):
        self.partner_id = partner_id

    def get_link_data(self, realm, link):
        """Возвращает словарь с данными партнёрской ссылки.

        :param RealmBase realm:
        :param PartnerLink link:
        :return:
        """

        link_url = link.url

        link_mutator = self.link_mutator.replace('{partner_id}', self.partner_id)
        if '?' in link_url and link_mutator.startswith('?'):
            link_mutator = link_mutator.replace('?', '&')

        url = '%s%s' % (link_url, link_mutator)

        title = '%s на %s' % (realm.model.get_verbose_name(), self.title)
        description = link.description
        if description:
            title = '%s — %s' % (title, description)

        page_soup = self.get_page_soup(link_url)

        price = self.get_price(page_soup).lower().strip(' .').replace('руб', 'руб.')
        if price.isdigit():
            price += ' руб.'

        data = {
            'icon_url': 'https://favicon.yandex.net/favicon/%s' % self.title,
            'title': title,
            'url': url,
            'price': price,
            'time': now()
        }
        return data

    @classmethod
    def get_page(cls, url):
        return get_from_url(url)

    @classmethod
    def get_page_soup(cls, url):
        page = cls.get_page(url)
        return make_soup(page.text)

    @classmethod
    def get_price(cls, page_soup):
        return ''


class BooksRu(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта books.ru."""

    ident = 'booksru'
    title = 'books.ru'
    link_mutator = '?partner={partner_id}'

    change_location_url = "https://www.books.ru/change_region.php"
    locations = {
        'nsk': {'mainregion_other': 1, 'subregion_other': 277},
        'msk': {'mainregion_other': 1, 'subregion_other': 271},
        'ned': {'mainregion_other': 0, 'subregion_other': 157}
    }
    default_location = 'nsk'

    @classmethod
    def get_price(cls, page_soup):

        price = ''

        if page_soup:
            matches = page_soup.select('.item-price .yprice.price')
            if matches:
                price = matches[0].text

        return price

    @classmethod
    def get_page(cls, url):
        resp = get_from_url(
            cls.change_location_url,
            data=cls.locations[cls.default_location],
            params={'back_url': urlparse(url).path},
            method='post',
        )
        return resp


class LitRes(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта litres.ru."""

    ident = 'litres'
    title = 'litres.ru'
    link_mutator = '?lfrom={partner_id}'

    @classmethod
    def get_price(cls, page_soup):

        price = ''

        if page_soup:
            matches = page_soup.select('.block48')
            if matches:
                price = matches[0].text

        return price


class Ozon(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта ozon.ru."""

    ident = 'ozon'
    title = 'ozon.ru'
    link_mutator = '?partner={partner_id}'

    @classmethod
    def get_price(cls, page_soup):

        price = ''

        if page_soup:
            matches = page_soup.findAll('span', attrs={'itemprop': 'price', 'class': 'hidden'})

            if matches:
                price = matches[0].text

        return price


class ReadRu(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта ozon.ru."""

    ident = 'readru'
    title = 'read.ru'
    link_mutator = '?pp={partner_id}'

    @classmethod
    def get_price(cls, page_soup):

        price = ''

        if page_soup:
            matches = page_soup.select('.read2__book_price__fullprice')

            if not matches:
                matches = page_soup.select('.book_price3__fullprice')

            if matches:
                price = matches[0].text
                if price:
                    try:
                        price = price.encode('latin1').decode('cp1251').strip().split(' ')[0]
                    except UnicodeEncodeError:
                        pass

        return price


class LabirintRu(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта labirint.ru."""

    ident = 'labirint'
    title = 'labirint.ru'
    link_mutator = '?p={partner_id}'

    @classmethod
    def get_price(cls, page_soup):

        price = ''

        if page_soup:
            matches = page_soup.select('.buying-price-val-number')
            if matches:
                price = matches[0].text

        return price


def get_cache_key(instance):
    """Возвращает ключ записи кэша для указанного экземпляра сущности.

    :param instance:
    :return:
    """
    return 'partner_links|%s|%s' % (instance.__class__.__name__, instance.pk)


def init_partners_module():
    """Инициализирует объекты известных партнёров и заносит их в реестр.

    :return:
    """
    global _PARTNERS_REGISTRY

    if _PARTNERS_REGISTRY is not None:
        return

    _PARTNERS_REGISTRY = OrderedDict()

    PARTNER_CLASSES = [BooksRu, LitRes, Ozon, ReadRu, LabirintRu]

    partners_settings = settings.PARTNER_IDS

    for partner_class in PARTNER_CLASSES:
        ident = partner_class.ident
        if ident in partners_settings:
            _PARTNERS_REGISTRY[ident] = partner_class(partners_settings[ident])

    from ..models import PartnerLink

    def partner_links_cache_invalidate(*args, **kwargs):
        """Сбрасывает кеш партнёрских ссылок при изменении данных
         моделей сыылок или их удалении.

        :param args:
        :param kwargs:
        :return:
        """
        cache_key = get_cache_key(kwargs.get('instance').linked_object)
        cache.delete(cache_key)

    signals.post_save.connect(partner_links_cache_invalidate, sender=PartnerLink, weak=False)
    signals.post_delete.connect(partner_links_cache_invalidate, sender=PartnerLink, weak=False)

init_partners_module()


def get_partners_choices():
    """Возвращает варианты выбора известных партнёров для раскрывающихся списков.

    :return:
    """
    choices = []
    for partner in _PARTNERS_REGISTRY.values():
        choices.append((partner.ident, partner.title))

    return choices


def get_partner_links(realm, item):
    """Возвращает словарь с данными по партнёрским ссылкам,
    готовый для передачи в шаблон.

    :param RealmBase realm:
    :param RealmBaseModel|ModelWithPartnerLinks item:
    :return:
    """

    cache_key = get_cache_key(item)
    links_data = cache.get(cache_key)

    if links_data is None:
        links_data = []
        links = item.partner_links.order_by('partner_alias', 'description').all()
        for link in links:
            partner = _PARTNERS_REGISTRY.get(link.partner_alias)

            if partner:
                links_data.append(partner.get_link_data(realm, link))

        cache.set(cache_key, links_data, _CACHE_TIMEOUT)

    return {'links': links_data}
