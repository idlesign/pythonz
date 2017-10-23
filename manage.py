#!/usr/bin/env python
import os
import sys


if __name__ == '__main__':
    # Для правильного импорта модулей добавим пару путей в список поиска:
    PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
    sys.path = [os.path.dirname(PROJECT_PATH), PROJECT_PATH] + sys.path

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
