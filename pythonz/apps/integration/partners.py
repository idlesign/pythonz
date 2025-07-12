from decimal import Decimal
from typing import TYPE_CHECKING, NamedTuple, Union

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache
from django.db.models import signals
from django.utils.timezone import now
from requests import Response
from requests.exceptions import ConnectionError

from .utils import get_from_url, make_soup, run_threads

if TYPE_CHECKING:
    from ..generics.models import RealmBaseModel
    from ..generics.realms import RealmBase
    from ..models import ModelWithPartnerLinks, PartnerLink

_CACHE_TIMEOUT: int = 28800  # 8 часов


class PartnerBase:
    """Базовый класс для работы с партнёрскими сайтами."""

    alias: str = None
    title: str = None
    link_mutator: str = None

    registry: dict[str, 'PartnerBase'] = {}
    """Реестр объектов партнёров."""

    def __init__(self, partner_id: str):
        self.partner_id = partner_id

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        alias = cls.alias
        partner_id = settings.PARTNER_IDS.get(alias, '')
        cls.registry[alias] = cls(partner_id)

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
    def get_page_soup(cls, url: str) -> BeautifulSoup | None:

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

    alias: str = 'booksru'
    title: str = 'books.ru'
    link_mutator: str = '?partner={partner_id}'

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:

        price = ''

        if page_soup:
            if matches := page_soup.select('h3.book-price'):
                price = matches[0].text

        return price


class LitRes(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта litres.ru."""

    alias: str = 'litres'
    title: str = 'litres.ru'
    link_mutator: str = '?lfrom={partner_id}'

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:

        price = ''

        if page_soup:
            if matches := page_soup.select('.simple-price'):
                price = matches[0].text

        return price


class Ozon(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта ozon.ru."""

    alias: str = 'ozon'
    title: str = 'ozon.ru'
    link_mutator: str = '?partner={partner_id}'

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:

        price = ''

        if page_soup:
            if matches := page_soup.findAll('span', attrs={'itemprop': 'price', 'class': 'hidden'}):
                price = matches[0].text

        return price


class Book24(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта book24.ru (бывший read.ru)."""

    alias: str = 'book24'
    title: str = 'book24.ru'
    link_mutator: str = (
            '?utm_source=affiliate&utm_medium=cpa&utm_campaign={partner_id}&'
            'utm_content=site&partnerId={partner_id}')

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:

        price = ''

        if page_soup:

            if match := page_soup.find(itemprop='price'):
                price = match.get('content', '').replace(' ', '')

        return price


class Bookvoed(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта bookvoed.ru."""

    alias: str = 'bookvoed'
    title: str = 'bookvoed.ru'
    link_mutator: str = '?{partner_id}'  # нет партнёрской программы

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:

        price = ''

        if page_soup:

            if match := page_soup.find(itemprop='price'):
                price = match.attrs.get('content') or ''
                if price:
                    price = f'{int(Decimal(price))}'

        return price


class LabirintRu(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта labirint.ru."""

    alias: str = 'labirint'
    title: str = 'labirint.ru'
    link_mutator: str = '?p={partner_id}'

    @classmethod
    def get_price(cls, page_soup: BeautifulSoup) -> str:

        price = ''

        if page_soup:
            if matches := page_soup.select('.buying-price-val-number'):
                price = matches[0].text

        return price


def get_cache_key(instance: 'RealmBaseModel') -> str:
    """Возвращает ключ записи кэша для указанного экземпляра сущности.

    :param instance:

    """
    return f'partner_links|{instance.__class__.__name__}|{instance.pk}'


def init_partners_module():
    """Инициализирует объекты известных партнёров и заносит их в реестр."""
    from ..models import PartnerLink  # noqa: PLC0415

    def partner_links_cache_invalidate(*args, **kwargs):
        """Сбрасывает кеш партнёрских ссылок при изменении данных
         моделей ссылок или их удалении.

        """
        cache_key = get_cache_key(kwargs.get('instance').linked_object)
        cache.delete(cache_key)

    signals.post_save.connect(partner_links_cache_invalidate, sender=PartnerLink, weak=False)
    signals.post_delete.connect(partner_links_cache_invalidate, sender=PartnerLink, weak=False)


init_partners_module()


def get_partners_choices() -> list[tuple[str, str]]:
    """Возвращает варианты выбора известных партнёров для раскрывающихся списков."""
    choices = [
        (partner.alias, partner.title)
        for partner in PartnerBase.registry.values()
    ]
    return choices


def get_partner_links(realm: type['RealmBase'], item: Union['RealmBaseModel', 'ModelWithPartnerLinks']) -> dict:
    """Возвращает словарь с данными по партнёрским ссылкам,
    готовый для передачи в шаблон.

    :param  realm:
    :param item:

    """
    cache_key = get_cache_key(item)
    links_data = cache.get(cache_key)

    class Task(NamedTuple):
        link: str
        realm: str
        partner: str

    def contribute_info(task: Task):
        if data := task.partner.get_link_data(task.realm, task.link):
            links_data.append(data)

    if links_data is None:

        links_data = []
        get_partner = PartnerBase.registry.get
        tasks = [
            Task(
                link=link,
                realm=realm,
                partner=partner
            )
            for link in item.partner_links.order_by('partner_alias', 'description').all()
            if (partner := get_partner(link.partner_alias))
        ]

        if tasks:
            run_threads(tasks, contribute_info)

        cache.set(cache_key, links_data, _CACHE_TIMEOUT)

    return {'links': links_data}
