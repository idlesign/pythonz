import os
import sys

from django.core.wsgi import get_wsgi_application

# Для правильного импорта модулей добавим пару путей в список поиска:
PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
sys.path = [os.path.dirname(PROJECT_PATH), PROJECT_PATH] + sys.path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.dev')
application = get_wsgi_application()
