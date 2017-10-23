#
# Для конфигурирования в ходе разработки используйте этот файл, а не base.py
#
from .settings_base import *


DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
INTERNAL_IPS = ['127.0.0.1']
ADMINS = (('me', 'me@some.where'),)

TEMPLATES[0]['OPTIONS']['debug'] = True

# Обход ошибки импорта - ручное конфигурирование отладочной панели.
# https://github.com/django-debug-toolbar/django-debug-toolbar/issues/521.
DEBUG_TOOLBAR_PATCH_SETTINGS = False
MIDDLEWARE_CLASSES = ('debug_toolbar.middleware.DebugToolbarMiddleware',) + MIDDLEWARE_CLASSES
INSTALLED_APPS += ('debug_toolbar',)


LOGGERS.update({

})
