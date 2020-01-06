import os
import sys

from django.core.wsgi import get_wsgi_application
from raven.contrib.django.raven_compat.middleware.wsgi import Sentry

# Для правильного импорта модулей добавим пару путей в список поиска:
PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
sys.path = [os.path.dirname(PROJECT_PATH), PROJECT_PATH] + sys.path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
application = Sentry(get_wsgi_application())
