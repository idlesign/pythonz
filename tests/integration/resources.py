from pythonz.apps.integration.resources import PyDigestResource
import pytest


@pytest.mark.slow
def test_py_digest():
    entries = PyDigestResource.fetch_entries()
    assert entries
