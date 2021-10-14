from .sub_email import *


SOCKS5_PROXY = ''
"""Адрес socks5 для запросов во вне."""

PARTNER_IDS = {}
"""Здесь указываются партнёрские идентификаторы."""

GOOGLE_API_KEY = 'not_a_secret'
YANDEX_SEARCH_ID = 'not_a_secret'
YANDEX_GEOCODER_KEY = 'not_a_secret'

TELEGRAM_BOT_TOKEN = 'not_a_secret'
TELEGRAM_BOT_URL = 'not_a_secret'
TELEGRAM_GROUP = 'group_id or @channel_name'

VK_ACCESS_TOKEN = 'not_a_secret'
VK_GROUP = 'group id prefixed with -'

FB_ACCESS_TOKEN = 'not_a_secret'


# Сюда помещаются реквизиты для пользования соответствующими службами доставки сообщений (cм. sitemessages.py).
SITEMESSAGE_INIT_BUILTIN_MESSAGE_TYPES = False
SITEMESSAGE_SHORTCUT_EMAIL_MESSAGE_TYPE = 'simple'

SITEMESSAGES_SETTINGS = {
    'twitter': [],
    'smtp': [
        SERVER_EMAIL,
        EMAIL_HOST_USER,
        EMAIL_HOST_PASSWORD,
        EMAIL_HOST,
        None,
        EMAIL_USE_TLS
    ],
    'telegram': [TELEGRAM_BOT_TOKEN],
    'fb': [FB_ACCESS_TOKEN],
    'vk': [VK_ACCESS_TOKEN],
}

SITEGATE_REMOTES = {
    'yandex': 'not_a_secret',
    'google': 'not_a_secret',
}
"""Идентификаторы клиентов для внешней авторизации."""
