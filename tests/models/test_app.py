import pytest

from pythonz.apps.models import App


@pytest.mark.slow
def test_basic(robot):

    app1 = App.objects.create(slug='pytest-djangoapp', submitter=robot, status=App.Status.PUBLISHED)
    app2 = App.objects.create(slug='srptools', submitter=robot, status=App.Status.PUBLISHED)

    updated = App.actualize_downloads()

    assert updated == 2

    app1.refresh_from_db()
    app2.refresh_from_db()

    assert app1.downloads
    assert app2.downloads
