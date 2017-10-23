"""
Этот модуль является единой точкой входа для конфигураций.

Функция import_by_environment() подгрузит сюда символы из модулей для текущей среды.
Например, для среды разработки подгрузится settings_development.py.
"""
from envbox import import_by_environment, get_environment


current_env = import_by_environment(get_environment(detectors_opts={'file': {'source': '../conf/environment'}}))

print('Environment type: %s' % current_env)
