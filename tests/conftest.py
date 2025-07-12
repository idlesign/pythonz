import os

import pytest
from pytest_djangoapp import configure_djangoapp_plugin

# Используем имитатор вместо uwsgi.
os.environ['UWSGICONF_FORCE_STUB'] = '1'

pytest_plugins = configure_djangoapp_plugin(
    settings='pythonz.settings.env_testing',
    admin_contrib=True,
    migrate=False,
)


@pytest.fixture
def robot(user_create, settings):
    """Возвращает объект пользователя-робота (суперпользователь)."""
    return user_create(attributes={'id': settings.ROBOT_USER_ID}, superuser=True)


@pytest.fixture
def mock_get_location(monkeypatch):
    monkeypatch.setattr(
        'pythonz.apps.models.place.get_location_data', lambda location_name: {})
