#
# Этот файл конфигурации используется для тестов.
#
from .settings_base import *

SITEPREFS_DISABLE_AUTODISCOVER = True
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}

