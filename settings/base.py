#
# Для конфигурирования в ходе разработки используйте dev.py, а не этот файл.
#
from os.path import dirname

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS


PATH_PROJECT = dirname(dirname(__file__))
PATH_DATA = '%s/data' % PATH_PROJECT

####################################################################

SITE_URL = 'http://pythonz.net'

PROJECT_SOURCE_URL = 'https://github.com/idlesign/pythonz'
DEBUG = True

SECRET_KEY = 'not_a_secret'
ADMINS = ()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '%s/db/data.db' % PATH_DATA,
    }
}

# Сюда помещаются реквизиты для пользования соответствующими службами доставки сообщений (cм. sitemessages.py).
SITEMESSAGES_SETTINGS = {
    'twitter': [],
    'smtp': [],
    'telegram': [],
}


# Здесь указываются партнёрские идентификаторы.
PARTNER_IDS = {}


GOOGLE_API_KEY = 'not_a_secret'
YANDEX_RCA_KEY = 'not_a_secret'
YANDEX_SEARCH_ID = 'not_a_secret'

# Переводит проект в агрессивный режим: задействует различную машинерию для привлечения внимания к проекту.
AGRESSIVE_MODE = False

####################################################################

SITEMESSAGE_INIT_BUILTIN_MESSAGE_TYPES = False
SITEMESSAGE_DEFAULT_SHORTCUT_EMAIL_MESSAGES_TYPE = 'simple'
ROBOTS_CACHE_TIMEOUT = 24 * 60 * 60

MANAGERS = ADMINS

SITE_ID = 1

AUTH_USER_MODEL = 'apps.User'

TIME_ZONE = 'Asia/Novosibirsk'
LANGUAGE_CODE = 'ru'
ROOT_URLCONF = 'urls'
WSGI_APPLICATION = 'wsgi.application'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

USE_I18N = True
USE_L10N = True
USE_TZ = True

ADMIN_URL = 'admin'

MEDIA_ROOT = '%s/media/' % PATH_DATA
MEDIA_URL = '/media/'

STATIC_ROOT = '%s/static/' % PATH_DATA
STATIC_URL = '/static/'
STATICFILES_DIRS = ('%s/static_src/' % PATH_DATA,)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'apps.middleware.TimezoneMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
)


TEMPLATE_DEBUG = DEBUG
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
TEMPLATE_CONTEXT_PROCESSORS += ('django.core.context_processors.request',)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',

    'apps',

    'admirarchy',
    'sitecats',
    'siteflags',
    'sitetree',
    'siteblocks',
    'sitegate',
    'sitemetrics',
    'siteprefs',
    'sitemessage',
    'xross',
    'etc',

    'datetimewidget',
    'simple_history',
    'robots',
)


if DEBUG:
    # Обход ошибки импорта - ручное конфигурирование отладочной панели.
    # https://github.com/django-debug-toolbar/django-debug-toolbar/issues/521.
    DEBUG_TOOLBAR_PATCH_SETTINGS = False
    MIDDLEWARE_CLASSES = ('debug_toolbar.middleware.DebugToolbarMiddleware',) + MIDDLEWARE_CLASSES
    INSTALLED_APPS += ('debug_toolbar',)
    # INSTALLED_APPS += ('debug_toolbar.apps.DebugToolbarConfig',)
    INTERNAL_IPS = ['127.0.0.1']
