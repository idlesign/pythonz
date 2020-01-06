import os
import sys
from pathlib import Path

from pytest_djangoapp import configure_djangoapp_plugin

# Имспользуем имитатор вместо uwsgi.
os.environ['UWSGICONF_FORCE_STUB'] = '1'


PROJECT_PATH = Path(__file__).absolute().parent.parent

sys.path = [
    f'{PROJECT_PATH.parent}',
    f'{PROJECT_PATH}',
] + sys.path


def hook(settings):
    from importlib import import_module

    settings_path = 'settings.settings_testing'

    if settings_path:
        settings_module = import_module(settings_path)
        settings_dict = {k: v for k, v in settings_module.__dict__.items() if k.upper() == k}
        settings.update(settings_dict)
        return settings

    return {}


pytest_plugins = configure_djangoapp_plugin(
    admin_contrib=True,
    settings_hook=hook,
    migrate=False,
)
