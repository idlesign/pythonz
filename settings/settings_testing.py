#
# Этот файл конфигурации используется для тестов.
#
from .settings_base import *

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}

