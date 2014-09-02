"""
Здесь настраиваются средства доставки сообщений.
Конфигурирование производится в settings.py проекта.
"""
from sitemessage.utils import register_messenger_objects
from django.conf import settings


SETTINGS = settings.SITEMESSAGES_SETTINGS
SETTINGS_TWITTER = SETTINGS['twitter']
SETTINGS_SMTP = SETTINGS['smtp']


messengers = []
if SETTINGS_TWITTER:
    from sitemessage.messengers.twitter import TwitterMessenger
    messengers.append(TwitterMessenger(*SETTINGS_TWITTER))

if SETTINGS_SMTP:
    from sitemessage.messengers.smtp import SMTPMessenger
    messengers.append(SMTPMessenger(*SETTINGS_SMTP))

if messengers:
    register_messenger_objects(*messengers)
