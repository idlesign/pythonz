#
# Для конфигурирования в ходе разработки используйте этот файл, а не settings_base.py
#
from .base import *

DEBUG = True
SITE_URL = 'http://localhost:8000'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '[::1]',
]

INTERNAL_IPS = [
    '127.0.0.1',
    '[::1]',
]


ADMINS = (
    ('me', 'me@some.where'),
)

TEMPLATES[0]['OPTIONS']['debug'] = True

INSTALLED_APPS.append('debug_toolbar')
MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

LOGGERS.update({

})


CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
