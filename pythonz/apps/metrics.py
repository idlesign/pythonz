from sitemetrics.providers import Yandex


class MyYandex(Yandex):
    """Модифицированный класс управления счётчиком.
    Подключаем некоторые плюшки из тех, что умеет счётчик.
    """

    params = {
        'webvisor': True,
        'clickmap': True,
        'track_links': True,
        'accurate_bounce': True,
        'no_index': False,
        'track_hash': False,
        'xml': False,
        'user_params': False,
    }
