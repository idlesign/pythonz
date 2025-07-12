import pytest
from django.utils import timezone

from pythonz.apps.integration.summary import Discuss, GithubTrending, Lwn, MailarchConferences, Psf, Stackoverflow

pytestmark = [pytest.mark.slow]


def test_lwn():

    results, latest = Lwn(
        previous_result=[],
        previous_dt=None
    ).run()

    assert isinstance(results, list)
    assert isinstance(latest, dict)
    assert results

    results, latest = Lwn(
        previous_result=latest,
        previous_dt=None
    ).run()
    assert isinstance(results, list)
    assert isinstance(latest, dict)
    assert not results


def test_pipermail():

    current, latest = MailarchConferences(
        previous_result=[],
        previous_dt=None,
        year_month='2009-May'
    ).run()

    assert len(current) == 7
    assert not current[0].title.startswith('[')
    assert len(latest) == 1
    assert latest[0] == 'https://mail.python.org/pipermail/conferences/2009-May/000016.html'

    prev_result = ['https://mail.python.org/pipermail/conferences/2009-May/000009.html']

    current, latest = MailarchConferences(
        previous_result=prev_result,
        previous_dt=None,
        year_month='2009-May'
    ).run()

    assert len(current) == 4
    assert len(latest) == 1

    MailarchConferences(
        previous_result=['faked'],
        previous_dt=None
    ).run()

    assert len(latest) == 1


def test_discuss():

    current, latest = Discuss(
        previous_result=[],
        previous_dt=None,
    ).run()

    assert current
    assert latest


def test_psf():

    current, latest = Psf(
        previous_result=[],
        previous_dt=None,
    ).run()

    assert current
    assert latest

    current_2, latest_2 = Psf(
        previous_result=latest,
        previous_dt=None,
    ).run()

    assert latest == latest_2
    assert current_2 == []


def test_github():

    current, latest = GithubTrending(
        previous_result=[],
        previous_dt=None
    ).run()

    assert current

    len_latest = len(latest)
    len_current = len(current)

    assert len_latest == len_current

    one_latest = latest.pop()

    current, latest = GithubTrending(
        previous_result=latest,
        previous_dt=None
    ).run()

    assert len(current) == 1
    assert len(latest) == 1
    assert one_latest in latest


@pytest.mark.skip('403 ошибка при получении csv')
def test_stack():

    current, latest = Stackoverflow(
        previous_result=[],
        previous_dt=None
    ).run()

    assert len(latest)

    current, latest = Stackoverflow(
        previous_result=[],
        previous_dt=timezone.now()
    ).run()

    assert not len(latest)  # за сегодня ещё нет вопросов
