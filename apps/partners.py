from collections import OrderedDict
from urllib.parse import urljoin

from django.conf import settings
from django.db.models import signals
from django.core.cache import cache

from .utils import make_soup


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

        url = '%s%s' % (link_url, self.link_mutator.replace('{partner_id}', self.partner_id))
        description = link.description

        if description:
            title = '%s: %s' % (self.title, description)
        else:
            title = '%s на %s' % (realm.model.get_verbose_name(), self.title)

        page_soup = self.get_page_soup(link_url)

        data = {
            'icon_url': self.get_icon_url(page_soup, link_url),
            'title': title,
            'url': url,
            'price': self.get_price(page_soup)
        }
        return data

    @classmethod
    def get_page_soup(cls, url):
        return make_soup(url)

    @classmethod
    def get_price(cls, page_soup):
        return ''

    @classmethod
    def get_icon_url(cls, page_soup, page_url):
        icon_url = ''

        if page_soup:
            matches = page_soup.find_all(attrs={'rel': 'shortcut icon'})
            if matches:
                href = matches[0].attrs['href']
                if href:
                    icon_url = urljoin(page_url, href)

        return icon_url


class BooksRu(PartnerBase):
    """Класс реализует работу по партнёрской программе сайта Books.ru."""

    ident = 'booksru'
    title = 'books.ru'
    link_mutator = '?partner={partner_id}'

    @classmethod
    def get_price(cls, page_soup):

        price = ''

        if page_soup:
            matches = page_soup.select('.yprice.price')
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

    PARTNER_CLASSES = [BooksRu]

    partners_settings = settings.PARTNER_IDS

    for partner_class in PARTNER_CLASSES:
        ident = partner_class.ident
        if ident in partners_settings:
            _PARTNERS_REGISTRY[ident] = partner_class(partners_settings[ident])

    from .models import PartnerLink

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
        links = item.partner_links.all()
        for link in links:
            partner = _PARTNERS_REGISTRY.get(link.partner_alias)

            if partner:
                links_data.append(partner.get_link_data(realm, link))

        cache.set(cache_key, links_data, _CACHE_TIMEOUT)

    return {'links': links_data}
