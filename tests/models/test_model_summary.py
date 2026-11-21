from pythonz.apps.integration.summary.base import SummaryItem
from pythonz.apps.models import Category, Summary


def test_create_article(robot):
    Category(creator=robot).save()
    article = Summary.create_article({
        'psf': [
            SummaryItem('https://some.iii/a/b', 'This| nice', 'do ` best'),
            SummaryItem('https://other.iii/d/f', 'title', 'descr'),
        ]
    })
    assert article
    assert article.text_src == (
        '#### Блог PSF\n|  |\n|---|\n'
        '| [This nice](https://some.iii/a/b) — do  best |\n| [title](https://other.iii/d/f) — descr |\n\n\n')
