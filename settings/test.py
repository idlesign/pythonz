#
# Этот файл конфигурации используется для тестов.
#
from .base import *

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}

