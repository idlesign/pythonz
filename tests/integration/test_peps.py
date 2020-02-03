import pytest

from pythonz.apps.integration.peps import strip_mail, sync


def test_strip_mail():

    result = strip_mail('Victor Stinner <victor.stinner at gmail.com>')

    assert result == ['Victor Stinner']

    result = strip_mail('Barry Warsaw, Jeremy Hylton, David Goodger, Nick Coghlan')

    assert result == ['Barry Warsaw', 'Jeremy Hylton', 'David Goodger', 'Nick Coghlan']

    result = strip_mail('paul at prescod.net (Paul Prescod)')

    assert result == ['Paul Prescod']

    result = strip_mail(
        'Guido van Rossum <guido at python.org>, '
        'Barry Warsaw <barry at python.org>, '
        'Nick Coghlan <ncoghlan at gmail.com>')

    assert result == ['Guido van Rossum', 'Barry Warsaw', 'Nick Coghlan']


@pytest.mark.slow
def test_sync(robot):
    synced = sync(limit=3, skip_deadend_peps=True)
    assert len(synced) == 3
