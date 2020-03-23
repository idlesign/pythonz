from unittest.mock import Mock

import pytest

from pythonz.apps.realms import BookRealm, Book
from pythonz.apps.integration import partners
from pythonz.apps.integration.partners import get_partner_links
from pythonz.apps.models import PartnerLink


@pytest.fixture
def assert_link_data():

    def assert_link_data_(partner_cls, url):
        partner = partner_cls(partner_id='dummy')

        data = partner.get_link_data(Mock(), PartnerLink(url=url))

        assert "руб" in data['price']
        assert 'dummy' in data['url']

        return data

    return assert_link_data_


@pytest.mark.slow
def test_get_links(robot):

    book = Book()
    book.save()

    urls = [
        ('booksru', 'https://www.books.ru/books/bibliya-705085/'),
        ('litres', 'https://www.litres.ru/mark-summerfield/programmirovanie-na-python-3-podrobnoe-rukovodstvo-24499518/'),
    ]

    links = []

    for alias, url in urls:
        link = PartnerLink(url=url, partner_alias=alias)
        link.linked_object = book
        link.save()
        links.append(link)

    data = get_partner_links(BookRealm, book)
    assert len(data['links']) == 2


@pytest.mark.slow
def test_booksru(assert_link_data):

    data = assert_link_data(
        partners.BooksRu, 'https://www.books.ru/books/bibliya-705085/')

    assert 'https://favicon.yandex.net/favicon/books.ru' == data['icon_url']


@pytest.mark.slow
def test_litres(assert_link_data):

    assert_link_data(
        partners.LitRes,
        'https://www.litres.ru/mark-summerfield/programmirovanie-na-python-3-podrobnoe-rukovodstvo-24499518/')
