"""
Здесь настраиваются средства доставки сообщений.
Конфигурирование производится в settings.py проекта.
"""
from sitemessage.utils import register_messenger_objects, register_message_types, override_message_type_for_app
from sitemessage.messages import EmailHtmlMessage, PlainTextMessage
from django.conf import settings


def register_messengers():
    """Регистрирует средства отсылки сообщений.

    :return:
    """

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

register_messengers()


class PythonzTwitterMessage(PlainTextMessage):
    """Базовый класс для сообщений, рассылаемых pythonz в Twitter."""

    priority = 1  # Рассылается ежеминутно.
    send_retry_limit = 5


class PythonzEmailMessage(EmailHtmlMessage):
    """Базовый класс для сообщений, рассылаемых pythonz по электронной почте.

    Этот же класс используется для рассылки писем от sitegate,

    """

    alias = 'simple'
    priority = 1  # Рассылается ежеминутно.
    send_retry_limit = 4

    def __init__(self, subject, html_or_dict, template_path=None):
        if not isinstance(html_or_dict, dict):
            html_or_dict = {'text': html_or_dict.replace('\n', '<br>')}
        super(PythonzEmailMessage, self).__init__(subject, html_or_dict, template_path=template_path)


class PythonzEmailNewEntity(PythonzEmailMessage):
    """Оповещение администраторам о добавлении новой сущности."""

    alias = 'new_entity'


class PythonzEmailDigest(PythonzEmailMessage):
    """Класс реализующий рассылку с подборкой новых материалов сайта (дайджест)."""

    alias = 'digest'
    priority = 7  # Рассылается раз в семь дней.
    send_retry_limit = 1  # Нет смысла пытаться повторно неделю спустя.


# Регистрируем наши типы сообщений.
register_message_types(PythonzEmailMessage, PythonzEmailNewEntity, PythonzEmailDigest)


# Заменяем тип сообщений, отсылаемых sitegate на свой.
override_message_type_for_app('sitegate', 'email_plain', 'simple')
