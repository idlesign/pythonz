from typing import Optional, List, Tuple, Union

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache
from django.db.models import signals
from django.utils.timezone import now
from requests import Response
from requests.exceptions import ConnectionError

from .utils import make_soup, get_from_url

if False:  # pragma: nocover
    from ..generics.realms import RealmBase
    from ..generics.models import RealmBaseModel
    from ..models import PartnerLink, ModelWithPartnerLinks

_PARTNERS_REGISTRY: Optional[dict] = None
_CACHE_TIMEOUT: int = 28800  # 8 часов


class PartnerBase:
    """Базовый класс для работы с партнёрскими сайтами."""

    ident: str = None
    title: str = None
    link_mutator: str = None

    def __init__(self, partner_id: str):
        self.partner_id = partner_id

    def get_link_data(self, realm: 'RealmBase', link: 'PartnerLink') -> dict:
        """Возвращает словарь с данными партнёрской ссылки.

        :param realm:
        :param link:

        """
        link_url = link.url

        link_mutator = self.link_mutator.replace('{partner_id}', self.partner_id)

        if '?' in link_url and link_mutator.startswith('?'):
            link_mutator = link_mutator.replace('?', '&')

        url = f'{link_url}{link_mutator}'

        title = f'{realm.model.get_verbose_name()} на {self.title}'
        description = link.description

        if description:
            title = f'{title} — {description}'

        page_soup = self.get_page_soup(link_url)

        if not page_soup:
            return {}

        price = self.get_price(
            page_soup
        ).lower().strip(' .').replace('руб', 'руб.').replace('₽', 'руб.').strip()

        if price.isdigit():
            price += ' руб.'

        data = {
            'icon_url': f'https://favicon.yandex.net/favicon/{self.title}',
            'title': title,
            'url': url,
            'price': price,
            'time': now()
        }
        return data

    @classmethod
    def get_page(cls, url: str) -> Response:
        return get_from_url(url, timeout=20)

    @classmethod
    def get_page_soup(cls, url: str) -> Optional[BeautifulSoup]:

        try:
            page = cls.get_page(url)

        except ConnectionError:
            return

        return make_soup(page.text)

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:
        return ''


class BooksRu(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта books.ru."""

    ident: str = 'booksru'
    title: str = 'books.ru'
    link_mutator: str = '?partner={partner_id}'

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:

        price = ''

        if page_soup:
            matches = page_soup.select('h3.book-price')

            if matches:
                price = matches[0].text

        return price


class LitRes(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта litres.ru."""

    ident: str = 'litres'
    title: str = 'litres.ru'
    link_mutator: str = '?lfrom={partner_id}'

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:

        price = ''

        if page_soup:
            matches = page_soup.select('.simple-price')

            if matches:
                price = matches[0].text

        return price


class Ozon(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта ozon.ru."""

    ident: str = 'ozon'
    title: str = 'ozon.ru'
    link_mutator: str = '?partner={partner_id}'

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:

        price = ''

        if page_soup:
            matches = page_soup.findAll('span', attrs={'itemprop': 'price', 'class': 'hidden'})

            if matches:
                price = matches[0].text

        return price


class ReadRu(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта ozon.ru."""

    ident: str = 'readru'
    title: str = 'read.ru'
    link_mutator: str = '?pp={partner_id}'

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:

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

    ident: str = 'labirint'
    title: str = 'labirint.ru'
    link_mutator: str = '?p={partner_id}'

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:

        price = ''

        if page_soup:
            matches = page_soup.select('.buying-price-val-number')

            if matches:
                price = matches[0].text

        return price


def get_cache_key(instance: 'RealmBaseModel') -> str:
    """Возвращает ключ записи кэша для указанного экземпляра сущности.

    :param instance:

    """
    return f'partner_links|{instance.__class__.__name__}|{instance.pk}'


def init_partners_module():
    """Инициализирует объекты известных партнёров и заносит их в реестр."""

    global _PARTNERS_REGISTRY

    if _PARTNERS_REGISTRY is not None:
        return

    _PARTNERS_REGISTRY = {}

    PARTNER_CLASSES = [BooksRu, LitRes, Ozon, ReadRu, LabirintRu]

    partners_settings = settings.PARTNER_IDS

    for partner_class in PARTNER_CLASSES:
        ident = partner_class.ident
        if ident in partners_settings:
            _PARTNERS_REGISTRY[ident] = partner_class(partners_settings[ident])

    from ..models import PartnerLink

    def partner_links_cache_invalidate(*args, **kwargs):
        """Сбрасывает кеш партнёрских ссылок при изменении данных
         моделей ссылок или их удалении.

        """
        cache_key = get_cache_key(kwargs.get('instance').linked_object)
        cache.delete(cache_key)

    signals.post_save.connect(partner_links_cache_invalidate, sender=PartnerLink, weak=False)
    signals.post_delete.connect(partner_links_cache_invalidate, sender=PartnerLink, weak=False)


init_partners_module()


def get_partners_choices() -> List[Tuple[str, str]]:
    """Возвращает варианты выбора известных партнёров для раскрывающихся списков."""

    choices = []

    for partner in _PARTNERS_REGISTRY.values():
        choices.append((partner.ident, partner.title))

    return choices


def get_partner_links(realm: 'RealmBase', item: Union['RealmBaseModel', 'ModelWithPartnerLinks']) -> dict:
    """Возвращает словарь с данными по партнёрским ссылкам,
    готовый для передачи в шаблон.

    :param  realm:
    :param item:

    """
    cache_key = get_cache_key(item)
    links_data = cache.get(cache_key)

    if links_data is None:

        links_data = []
        links = item.partner_links.order_by('partner_alias', 'description').all()

        for link in links:
            partner = _PARTNERS_REGISTRY.get(link.partner_alias)

            if partner:
                data = partner.get_link_data(realm, link)

                if data:
                    links_data.append(data)

        cache.set(cache_key, links_data, _CACHE_TIMEOUT)

    return {'links': links_data}
