VERSION = (0, 30, 0)

# Конфигурация лежит здесь:
default_app_config = 'apps.config.PythonzAppsConfig'


from json import JSONEncoder


def patch_json_encoder():
    """Модифицирует базовый json-кодировщик, для поддержки метода
    to_json пользовательских типов.

    """
    def json_encoder_default(self, obj):
        return getattr(obj.__class__, 'to_json', json_encoder_default.default_)(obj)

    json_encoder_default.default_ = JSONEncoder().default
    JSONEncoder.default = json_encoder_default


patch_json_encoder()
