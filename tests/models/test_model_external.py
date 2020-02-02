import pytest

from pythonz.apps.models import ExternalResource


@pytest.mark.slow
def test_external():
    ExternalResource.fetch_new()
