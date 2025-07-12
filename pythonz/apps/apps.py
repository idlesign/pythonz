from django.apps import AppConfig


class PythonzAppsConfig(AppConfig):
    """Конфигурация прриложений pythonz."""

    name: str = 'pythonz.apps'
    verbose_name: str = 'Сущности pythonz'

    def ready(self):
        from .realms import get_realms  # noqa: PLC0415

        for realm in get_realms().values():
            # Привязываем область к моделям, она понадобится для вычисления URL.
            realm.model.realm = realm
