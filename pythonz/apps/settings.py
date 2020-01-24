"""Файл для siteprefs, чтобы настройки отображались в административном интерфейсе."""
from django.conf import settings


SOCKS5_PROXY = settings.SOCKS5_PROXY

GOOGLE_API_KEY = settings.GOOGLE_API_KEY
YANDEX_SEARCH_ID = settings.YANDEX_SEARCH_ID

TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_GROUP = settings.TELEGRAM_GROUP

VK_ACCESS_TOKEN = settings.VK_ACCESS_TOKEN
VK_GROUP = settings.VK_GROUP


if 'siteprefs' in settings.INSTALLED_APPS:

    from siteprefs.toolbox import preferences

    with preferences() as prefs:

        prefs(
            SOCKS5_PROXY,
            GOOGLE_API_KEY,
            YANDEX_SEARCH_ID,
            TELEGRAM_BOT_TOKEN,
            TELEGRAM_GROUP,
            VK_ACCESS_TOKEN,
            VK_GROUP,
        )
