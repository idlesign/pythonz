"""
Этот модуль является единой точкой входа для конфигураций.

Функция import_by_environment() подгрузит сюда символы из модулей для текущей среды.
Например, для среды разработки подгрузится settings_development.py.
"""
from envbox import import_by_environment, get_environment


current_env = import_by_environment(
    # For production one can place `/var/lib/pythonz/environ` file with `production` as it contents.
    get_environment(detectors_opts={'file': {'source': '/var/lib/pythonz/environ'}}))


IN_PRODUCTION = current_env == 'production'

print('# Environment type: %s' % current_env)