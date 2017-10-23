from django.apps import AppConfig


class PythonzAppsConfig(AppConfig):
    """Конфигурация прриложений pythonz."""

    name = 'apps'
    verbose_name = 'Сущности pythonz'

    def ready(self):
        from apps.realms import get_realms

        for realm in get_realms().values():
            # Привязываем область к моделям, она понадобится для вычисления URL.
            realm.model.realm = realm

        # Регистрируем фоновые задания, путём импорта любого символа.
        from .tasks import task_send_messages
