from pythonz.apps.integration.summary.base import SummaryItem
from pythonz.apps.models import Summary, Category


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
        '.. title:: Блог PSF\n.. table::\n'
        '`This nice<https://some.iii/a/b>`_ — do  best\n`title<https://other.iii/d/f>`_ — descr\n\n\n')
