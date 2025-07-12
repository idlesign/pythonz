"""
Этот модуль является единой точкой входа для конфигураций.

Функция import_by_environment() подгрузит сюда символы из модулей для текущей среды.
Например, для среды разработки подгрузится settings_development.py.
"""
from envbox import get_environment, import_by_environment

current_env = import_by_environment(
    # For production one can place `/var/lib/pythonz/environ` file with `production` as it contents.
    get_environment(detectors_opts={'file': {'source': '/var/lib/pythonz/environ'}}),
    module_name_pattern='env_%s'
)


IN_PRODUCTION = current_env == 'production'

print(f'# Environment type: {current_env}')
