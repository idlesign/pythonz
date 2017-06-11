from datetime import datetime

from pythonz.apps.integration.summary import MailarchConferences, GithubTrending, Stackoverflow


def test_pipermail():
    by_title, latest = MailarchConferences(None, None, year_month='2009-May').run()

    assert len(by_title) == 7
    assert not by_title.popitem()[0].startswith('[')
    assert len(latest) == 1
    assert latest[0] == 'https://mail.python.org/pipermail/conferences/2009-May/000016.html'

    prev_result = ['https://mail.python.org/pipermail/conferences/2009-May/000009.html']
    by_title, latest = MailarchConferences(prev_result, None, year_month='2009-May').run()

    assert len(by_title) == 4
    assert len(latest) == 1

    MailarchConferences(['faked'], None).run()

    assert len(latest) == 1


def test_github():
    by_title, latest = GithubTrending(None, None).run()
    len_latest = len(latest)
    len_by_title = len(by_title)

    assert len_latest == len_by_title

    one_latest = latest.pop()

    by_title, latest = GithubTrending(latest, None).run()

    assert len(by_title) == 1
    assert len(latest) == 1
    assert one_latest in latest


def test_stack():

    by_title, latest = Stackoverflow(None, None).run()

    assert len(latest)

    by_title, latest = Stackoverflow(None, previous_dt=datetime.now()).run()

    assert not len(latest)  # за сегодня ещё нет вопросов
