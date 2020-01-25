import pytest

from pythonz.apps.integration import partners
from pythonz.apps.models import PartnerLink


@pytest.mark.slow
def test_booksru(mocker):

    book_link = 'https://www.books.ru/books/nosql-novaya-metodologiya-razrabotki-nerelyatsionnykh-baz-dannykh-3195898'
    partner_id = '12345'
    booksru = partners.BooksRu(partner_id=partner_id)
    link = PartnerLink(url=book_link)
    mock_realm = mocker.Mock()

    data = booksru.get_link_data(mock_realm, link)

    assert "руб" in data['price']
    assert "%s?partner=%s" % (book_link, partner_id) == data['url']
    assert 'https://favicon.yandex.net/favicon/books.ru' == data['icon_url']

    # проверка валюты нидерландов
    partners.BooksRu.default_location = 'ned'
    data = booksru.get_link_data(mock_realm, link)

    assert "euro" in data['price']
