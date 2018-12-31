import sys
from os.path import dirname, abspath

from pytest_djangoapp import configure_djangoapp_plugin

PROJECT_PATH = dirname(dirname(abspath(__file__)))

sys.path = [dirname(PROJECT_PATH), PROJECT_PATH] + sys.path


def hook(settings):
    from importlib import import_module

    settings_path = 'settings.settings_testing'

    if settings_path:
        settings_module = import_module(settings_path)
        settings.update(settings_module.__dict__)
        return settings

    return {}


pytest_plugins = configure_djangoapp_plugin(
    admin_contrib=True,
    settings_hook=hook,
    migrate=False,
)
