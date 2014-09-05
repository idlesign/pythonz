"""
Здесь настраиваются средства доставки сообщений.
Конфигурирование производится в settings.py проекта.
"""
from sitemessage.utils import register_messenger_objects, register_message_types
from sitemessage.messages import EmailHtmlMessage, PlainTextMessage
from sitemessage.toolbox import schedule_messages, recipients
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
    """Базовый класс для сообщений, рассылаемых pythonz по электронной почте."""

    alias = 'simple'
    priority = 1  # Рассылается ежеминутно.
    send_retry_limit = 4


class PythonzEmailNewEntity(PythonzEmailMessage):
    """Оповещение администраторам о добавлении новой сущности."""

    alias = 'new_entity'


class PythonzEmailDigest(PythonzEmailMessage):
    """Класс реализующий рассылку с подборкой новых материалов сайта (дайджест)."""

    alias = 'digest'
    priority = 7  # Рассылается раз в семь дней.
    send_retry_limit = 1  # Нет смысла пытаться повторно неделю спустя.


register_message_types(PythonzEmailNewEntity, PythonzEmailDigest)


##########


def get_admins_emails():
    """Возвращает адреса электронной почты администраторов проекта.

    :return:
    """
    to = []
    for item in settings.ADMINS:
        to.append(item[1])  # Адрес электронной почты админа.
    return to


def get_email_full_subject(subject):
    """Возвращает полный заголовок для электронного письма.

    :param subject:
    :return:
    """
    return 'pythonz.net: %s' % subject


def notify_entity_published(entity):
    """Отсылает оповещение о публикации сущности.

    :param RealmBaseModel entity:
    :return:
    """
    message = 'Новое: %s «%s» %s' % (entity.get_verbose_name(), entity.title, entity.get_absolute_url())
    schedule_messages(PythonzTwitterMessage(message), recipients('twitter', ''))


def notify_new_entity(entity):
    """Отсылает оповещение о создании новой сущности.

    Рассылается администраторам проекта.

    :param RealmBaseModel entity:
    :return:
    """
    context = {
        'entity_title': entity.title,
        'entity_url': entity.get_absolute_url()
    }
    m = PythonzEmailNewEntity(get_email_full_subject('Добавлена новая сущность - %s' % entity.title), context)
    schedule_messages(m, recipients('smtp', get_admins_emails()))

