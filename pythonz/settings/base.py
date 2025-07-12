from .sub_paths import *  # noqa
from .sub_email import *  # noqa
from .sub_intergration import *  # noqa
from .sub_logging import *  # noqa
from .sub_security import *  # noqa
from .sub_sentry import init_sentry  # noqa

from pythonz import VERSION

SITE_URL = 'https://pythonz.net'
PROJECT_SOURCE_URL = 'https://github.com/idlesign/pythonz'
USER_AGENT = f'pythonz.net/{VERSION} (press@pythonz.net)'

ROBOT_USER_ID = 1
"""Идентификатор пользователя-робота."""

SUMMARY_CATEGORY_ID = 1
"""Идентификатор категории Сводок."""

AGRESSIVE_MODE = False
"""Переводит проект в агрессивный режим: задействует различную машинерию для привлечения внимания к проекту."""

DEBUG = False

ADMINS = ()
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': f'{PROJECT_DIR_STATE}/data.db',
    }
}


SITE_ID = 1

ROOT_URLCONF = 'pythonz.urls'
WSGI_APPLICATION = 'pythonz.wsgi.application'

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Asia/Novosibirsk'

USE_I18N = True
USE_L10N = True
USE_TZ = True

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'settings'
LOGOUT_REDIRECT_URL = 'index'

ADMIN_URL = 'admin'
MEDIA_URL = '/media/'
STATIC_URL = '/static/'


INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',

    'admirarchy',
    'siteajax',
    'sitecats',
    'siteflags',
    'sitetree',
    'siteblocks',
    'sitegate',
    'sitemetrics',
    'siteprefs',
    'sitemessage',
    'etc',

    'uwsgiconf.contrib.django.uwsgify',

    'simple_history',
    'robots',

    'pythonz.apps',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'pythonz.apps.middleware.TimezoneMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


ROBOTS_CACHE_TIMEOUT = 6 * 60 * 60

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
