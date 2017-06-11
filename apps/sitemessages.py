"""
Здесь настраиваются средства доставки сообщений.
Конфигурирование производится в settings.py проекта.
"""
from datetime import datetime, timedelta
from collections import OrderedDict
from functools import partial

from sitemessage.utils import register_messenger_objects, register_message_types, override_message_type_for_app
from sitemessage.messages.email import EmailHtmlMessage
from sitemessage.messages.plain import PlainTextMessage
from sitemessage.signals import sig_unsubscribe_failed, sig_unsubscribe_success
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.utils.text import Truncator

from .utils import get_datetime_from_till
from .realms import get_realms, get_realm
from .signals import sig_entity_published, sig_entity_new, sig_search_failed, sig_integration_failed, \
    sig_send_generic_telegram


def register_messengers():
    """Регистрирует средства отсылки сообщений.

    :return:
    """

    SETTINGS = settings.SITEMESSAGES_SETTINGS
    SETTINGS_TWITTER = SETTINGS['twitter']
    SETTINGS_SMTP = SETTINGS['smtp']
    SETTINGS_TELEGRAM = SETTINGS['telegram']
    SETTINGS_FB = SETTINGS['fb']
    SETTINGS_VK = SETTINGS['vk']

    messengers = []
    if SETTINGS_TWITTER:
        from sitemessage.messengers.twitter import TwitterMessenger
        messengers.append(TwitterMessenger(*SETTINGS_TWITTER))

    if SETTINGS_SMTP:
        from sitemessage.messengers.smtp import SMTPMessenger
        messengers.append(SMTPMessenger(*SETTINGS_SMTP))

    if SETTINGS_TELEGRAM:
        from sitemessage.messengers.telegram import TelegramMessenger
        messengers.append(TelegramMessenger(*SETTINGS_TELEGRAM))

    if SETTINGS_FB:
        from sitemessage.messengers.facebook import FacebookMessenger
        messengers.append(FacebookMessenger(*SETTINGS_FB))

    if SETTINGS_VK:
        from sitemessage.messengers.vkontakte import VKontakteMessenger
        messengers.append(VKontakteMessenger(*SETTINGS_VK))

    if messengers:
        register_messenger_objects(*messengers)

register_messengers()


def connect_signals():
    """Подключает обработчики сигналов, связанных с рассылками
    оповещений.

    :return:
    """

    def unsubscribe_failed(*args, **kwargs):
        messages.error(kwargs['request'], 'К сожалению, отменить подписку не удалось.', 'danger error')
    sig_unsubscribe_failed.connect(unsubscribe_failed, weak=False)

    def unsubscribe_success(*args, **kwargs):
        messages.success(kwargs['request'], 'Подписка успешно отменена. Спасибо, что читали!', 'success')
    sig_unsubscribe_success.connect(unsubscribe_success, weak=False)

    # Новый материал.
    notify_handler = lambda sender, **kwargs: PythonzEmailNewEntity.create(kwargs['entity'])
    sig_entity_new.connect(notify_handler, dispatch_uid='cfg_new_entity', weak=False)

    # Поиск без результатов.
    notify_handler = (
        lambda sender, **kwargs: PythonzEmailOneliner.create('Поиск без результатов', kwargs['search_term']))
    sig_search_failed.connect(notify_handler, dispatch_uid='cfg_search_failed', weak=False)

    # Ошибка интеграции со сторонними сервисами.
    notify_handler = (
        lambda sender, **kwargs: PythonzEmailOneliner.create('Ошибка интеграции', kwargs['description']))
    sig_integration_failed.connect(notify_handler, dispatch_uid='cfg_integration_failed', weak=False)

    # Сообщение в Телеграм.
    notify_handler = lambda sender, **kwargs: PythonzTelegramMessage.create(kwargs['text'])
    sig_send_generic_telegram.connect(notify_handler, dispatch_uid='cfg_telegram_generic', weak=False)

    # Материал опубликован.
    def notify_published(sender, **kwargs):
        entity = kwargs['entity']
        if not entity.notify_on_publish:
            return False

        PythonzTwitterMessage.create_published(entity)
        PythonzTelegramMessage.create_published(entity)
        PythonzFacebookMessage.create_published(entity)
        PythonzVkontakteMessage.create_published(entity)

    sig_entity_published.connect(notify_published, dispatch_uid='cfg_entity_published', weak=False)


connect_signals()


class PythonzBaseMessage(PlainTextMessage):
    """Базовый класс для сообщений о новых материалах."""

    alias = None
    supported_messengers = None

    priority = 1  # Рассылается ежеминутно.
    send_retry_limit = 5
    title = 'Оповещение'
    allow_user_subscription = False


class PythonzFacebookMessage(PythonzBaseMessage):
    """Класс для сообщений о новых материалах на сайте, публикуемых на стене в Facebook."""

    alias = 'fb_update'
    supported_messengers = ['fb']

    @classmethod
    def create_published(cls, entity):
        message = entity.get_absolute_url(with_prefix=True, utm_source='fb')
        cls.create(message)

    @classmethod
    def create(cls, message):
        cls(message).schedule(cls.recipients('fb', ''))


class PythonzVkontakteMessage(PythonzBaseMessage):
    """Класс для сообщений о новых материалах на сайте, публикуемых на стене в ВКонтакте."""

    alias = 'vk_update'
    supported_messengers = ['vk']

    @classmethod
    def create_published(cls, entity):
        message = entity.get_absolute_url(with_prefix=True, utm_source='vk')
        cls.create(message)

    @classmethod
    def create(cls, message):
        cls(message).schedule(cls.recipients('vk', settings.VK_GROUP))


class PythonzTwitterMessage(PythonzBaseMessage):
    """Базовый класс для сообщений, рассылаемых pythonz в Twitter."""

    supported_messengers = ['twitter']

    @classmethod
    def create_published(cls, entity):
        MAX_LEN = 139  # Максимальная длина твита. Для верности меньше.
        URL_SHORTENED_LEN = 30  # Максимальная длина сокращённого URL

        prefix = '%s «' % entity.get_verbose_name()
        postfix = '»'
        if settings.AGRESSIVE_MODE:
            postfix = '%s #python' % postfix

        title = Truncator(str(entity)).chars(MAX_LEN - URL_SHORTENED_LEN - len(prefix) - len(postfix))

        url = entity.get_absolute_url(with_prefix=True, utm_source='twee')
        message = '%s%s%s %s' % (prefix, title, postfix, url)

        cls.create(message)

    @classmethod
    def create(cls, message):
        cls(message).schedule(cls.recipients('twitter', ''))


class PythonzTelegramMessage(PythonzBaseMessage):
    """Класс для сообщений о новых материалах на сайте, рассылаемых pythonz в Telegram."""

    alias = 'tele_update'
    supported_messengers = ['telegram']

    @classmethod
    def create_published(cls, entity):
        message = 'Новое: %s «%s» %s' % (
            entity.get_verbose_name(), str(entity), entity.get_absolute_url(with_prefix=True))

        cls.create(message)

    @classmethod
    def create(cls, message):
        cls(message).schedule(cls.recipients('telegram', settings.TELEGRAM_GROUP))


class PythonzEmailMessage(EmailHtmlMessage):
    """Базовый класс для сообщений, рассылаемых pythonz по электронной почте.

    Этот же класс используется для рассылки писем от sitegate,

    """

    alias = 'simple'
    priority = 1  # Рассылается ежеминутно.
    send_retry_limit = 4
    title = 'Базовые оповещения'
    allow_user_subscription = False

    def __init__(self, subject, html_or_dict, template_path=None):
        if not isinstance(html_or_dict, dict):
            html_or_dict = {'text': html_or_dict.replace('\n', '<br>')}
        super().__init__(subject, html_or_dict, template_path=template_path)

    @classmethod
    def get_full_subject(cls, subject):
        """Возвращает полный заголовок для электронного письма.

        :param subject:
        :return:
        """
        return 'pythonz.net: %s' % subject

    @classmethod
    def get_admins_emails(cls):
        """Возвращает адреса электронной почты администраторов проекта.

        :return:
        """
        to = []
        for item in settings.ADMINS:
            to.append(item[1])  # Адрес электронной почты админа.
        return to


class PythonzEmailOneliner(PythonzEmailMessage):
    """Простое "однострочное" сообщение."""

    @classmethod
    def create(cls, subject, text):
        """Создаёт оповещение общего вида.

        Рассылается администраторам проекта.

        :param subject: Заголовок.
        :param text: Текст сообщения.
        :return:
        """
        cls(cls.get_full_subject(subject), text).schedule(cls.recipients('smtp', cls.get_admins_emails()))


class PythonzEmailNewEntity(PythonzEmailMessage):
    """Оповещение администраторам о добавлении новой сущности."""

    alias = 'new_entity'
    title = 'Новое на сайте'

    @classmethod
    def create(cls, entity):
        """Создаёт оповещение о создании новой сущности.

        Рассылается администраторам проекта.

        :param RealmBaseModel entity:
        :return:
        """
        if not entity.notify_on_publish:
            return False

        subject = cls.get_full_subject('Новое - %s' % entity)
        context = {
            'entity_title': str(entity),
            'entity_url': entity.get_absolute_url()
        }
        cls(subject, context).schedule(cls.recipients('smtp', cls.get_admins_emails()))


class PythonzEmailDigest(PythonzEmailMessage):
    """Класс реализующий рассылку с подборкой новых материалов сайта (сводку)."""

    alias = 'digest'
    priority = 7  # Рассылается раз в семь дней.
    send_retry_limit = 1  # Нет смысла пытаться повторно неделю спустя.
    title = 'Еженедельная сводка'
    allow_user_subscription = True

    @classmethod
    def create(cls):
        """Создаёт депеши для рассылки еженедельной сводки.

        Реальная компиляция сводки происходит в compile().

        :return:
        """
        format_date = lambda d: d.date().strftime('%d.%m.%Y')
        date_from, date_till = get_datetime_from_till(7)

        subject = cls.get_full_subject('Подборка материалов %s-%s' % (format_date(date_from), format_date(date_till)))
        context = {
            'date_from': date_from.timestamp(),
            'date_till': date_till.timestamp()
        }
        cls(subject, context).schedule(cls.get_subscribers())

    @classmethod
    def get_realms_data(cls, date_from, date_till, modified_mode=False):
        """Возвращает данные о материалах за указанный период.

        :param date date_from: Дата начала периода
        :param date date_till: Дата завершения периода
        :param bool modified_mode: Флаг. Следует ли возвращать данные об изменившихся материалах.
        :return:
        """
        if modified_mode:
            filter_kwargs = {
                'time_published__lte': date_from,
                'time_modified__gte': date_from,
                'time_modified__lte': date_till
            }

        else:
            filter_kwargs = {
                'time_published__gte': date_from,
                'time_published__lte': date_till
            }

        realms_data = OrderedDict()
        for realm in get_realms().values():
            cls.extend_realms_data(realms_data, realm, filter_kwargs, 'time_published')

        return realms_data

    @classmethod
    def extend_realms_data(cls, realms_data, realm, filter_kwargs, order_by):
        """Дополняет словарь с данными областей объектами из указанной области.
        Требуемые объекты определяются указанным фильтром.

        :param OrderedDict realms_data: Словарь с данными.
        :param BaseRealm realm: Область.
        :param dict filter_kwargs: Фильтр для получения объектов области.
        :param str order_by: Имя поля, по которому следует отсортировать объекты.
        :return:
        """
        if realm.ready_for_digest:
            entries = realm.model.get_actual().filter(**filter_kwargs).order_by(order_by)
            if entries:
                for entry in entries:
                    entry.absolute_url = entry.get_absolute_url(with_prefix=True, utm_source='mail')
                realms_data[realm.model.get_verbose_name_plural()] = entries

    @classmethod
    def get_upcoming_items(cls):
        """Возвращает данные о материалах которые вскоре станут актульными.
        Например, о грядущих событиях.

        :return:
        """

        date_from = timezone.now()
        date_till = date_from + timedelta(days=10)  # 10 дней, чтобы покрыть остаток текущей и следующую неделю.

        filter_kwargs = {
            'time_start__gte': date_from,
            'time_start__lte': date_till
        }

        realms_data = OrderedDict()

        realm = get_realm('event')
        cls.extend_realms_data(realms_data, realm, filter_kwargs, 'time_start')

        return realms_data

    @classmethod
    def get_template_context(cls, context):
        """Заполняет шаблон сообщения данными.

        :param context:
        :return:
        """
        get_date = partial(datetime.fromtimestamp, tz=timezone.get_current_timezone())
        date_from = get_date(context.get('date_from'))
        date_till = get_date(context.get('date_till'))

        realms_data = OrderedDict()

        objects_upcoming = cls.get_upcoming_items()
        if objects_upcoming:
            realms_data['Скоро'] = objects_upcoming

        objects_new = cls.get_realms_data(date_from, date_till)
        if objects_new:
            realms_data['Новые'] = objects_new

        objects_modified = cls.get_realms_data(date_from, date_till, modified_mode=True)
        if objects_modified:
            realms_data['Изменившиеся'] = objects_modified

        context.update({'realms_data': realms_data})
        return context


# Регистрируем наши типы сообщений.
register_message_types(
    PythonzTwitterMessage,
    PythonzTelegramMessage,
    PythonzFacebookMessage,
    PythonzVkontakteMessage,
    PythonzEmailMessage,
    PythonzEmailOneliner,
    PythonzEmailNewEntity,
    PythonzEmailDigest
)


# Заменяем тип сообщений, отсылаемых sitegate на свой.
override_message_type_for_app('sitegate', 'email_plain', 'simple')
