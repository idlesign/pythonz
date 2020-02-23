import pytest

from pythonz.apps.models import Vacancy


@pytest.mark.slow
def test_vacancy():
    Vacancy.fetch_items()
