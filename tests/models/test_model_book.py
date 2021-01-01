from pythonz.apps.models import Book


def test_partner_links_enrich(robot):
    data = {
        'первая': {
            'здесь1': 'booksru',
            'здесь2': 'booksru',
            'там1': 'litres',
        },
    }
    links = Book.partner_links_enrich(data)

    assert Book.objects.count() == 1

    assert len(links) == 3
    link = links[0]
    assert link.url == 'здесь1'
    assert link.partner_alias == 'booksru'

    data.update({
        'первая': {
            'здесь3': 'booksru',  # добавится эта ссылка.
        },
        'тоже первая': {
            'здесь2': 'booksru',
        },
        'третья': {  # и эта книга.
            'там2': 'litres',  # и эта ссылка
        },
    })
    links = Book.partner_links_enrich(data)
    assert Book.objects.count() == 2
    assert len(links) == 2
