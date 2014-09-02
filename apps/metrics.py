from sitemetrics.providers import Yandex


class MyYandex(Yandex):
    """Модифицированный класс управления счётчиком.
    Подключаем все возможные плюшки, которые умеет счётчик.

    """

    @classmethod
    def get_params(cls):
        return {}
