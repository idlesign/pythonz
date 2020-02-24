import pytest
from django.db import IntegrityError

from pythonz.apps.models import Event


def test_event_unique_source(robot):
    Event.objects.create(submitter=robot, src_alias='one', src_id='10')

    with pytest.raises(IntegrityError):
        Event.objects.create(submitter=robot, src_alias='one', src_id='10')


@pytest.mark.slow
def test_event_fetch_items(robot, mock_get_location):
    Event.fetch_items()
