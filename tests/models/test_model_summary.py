from pythonz.apps.models import Summary, Category


def test_create_article(robot):
    Category(creator=robot).save()
    article = Summary.create_article({})
    assert article
