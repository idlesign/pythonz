from unittest.mock import Mock

import pytest

from pythonz.apps.integration import partners
from pythonz.apps.models import PartnerLink


@pytest.mark.slow
def test_booksru():

    book_link = 'https://www.books.ru/books/bibliya-705085/'
    partner_id = '12345'
    booksru = partners.BooksRu(partner_id=partner_id)
    link = PartnerLink(url=book_link)
    mock_realm = Mock()

    data = booksru.get_link_data(mock_realm, link)

    assert "руб" in data['price']
    assert "%s?partner=%s" % (book_link, partner_id) == data['url']
    assert 'https://favicon.yandex.net/favicon/books.ru' == data['icon_url']
