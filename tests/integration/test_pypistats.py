import pytest

from pythonz.apps.integration.pypistats import get_for_package


@pytest.mark.slow
def test_basic():

    data = get_for_package('django-sitetree')
    assert data
    assert data.popitem()[1] > 0
