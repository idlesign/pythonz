import pytest
from django.db import IntegrityError

from pythonz.apps.models import Vacancy


def test_vacancy_unique_source(robot):
    Vacancy.objects.create(submitter=robot, src_alias='one', src_id='10')

    with pytest.raises(IntegrityError):
        Vacancy.objects.create(submitter=robot, src_alias='one', src_id='10')


@pytest.mark.slow
def test_vacancy_fetch_items(mock_get_location):
    Vacancy.fetch_items()
