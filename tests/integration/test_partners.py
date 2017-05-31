

def test_booksru(mocker):
    from apps.integration import partners
    from apps.models import PartnerLink

    book_link = 'https://www.books.ru/books/nosql-novaya-metodologiya-razrabotki-nerelyatsionnykh-baz-dannykh-3195898'
    partner_id = '12345'
    booksru = partners.BooksRu(partner_id=partner_id)
    link = PartnerLink(url=book_link)
    mock_realm = mocker.Mock()

    data = booksru.get_link_data(mock_realm, link)

    assert "руб" in data['price']
    assert "%s?partner=%s" % (book_link, partner_id) == data['url']
    assert 'https://www.books.ru/static/images/favicon.ico' == data['icon_url']

    # проверка валюты нидерландов
    partners.BooksRu.default_location = 'ned'
    data = booksru.get_link_data(mock_realm, link)

    assert "euro" in data['price']
