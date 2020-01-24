from functools import lru_cache
from typing import List, Union

import telebot
from bleach import clean
from django.conf import settings
from django.http import HttpRequest
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, InlineQuery

from ..generics.models import RealmBaseModel, CommonEntityModel
from ..models import Reference, PEP
from ..utils import get_logger
from ..utils import truncate_chars
from ..zen import ZEN

LOGGER = get_logger('telebot')


socks_proxy = settings.SOCKS5_PROXY

if socks_proxy:
    telebot.apihelper.proxy = {'https': f'socks5://{socks_proxy}'}


bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN, threaded=False)


def get_webhook_url() -> str:
    """Возвращает webhook URL."""
    return f"{settings.SITE_URL.replace('http', 'https')}/{settings.TELEGRAM_BOT_URL}/"


def set_webhook() -> dict:
    """Конфигурирует механизм webhook."""

    certificate = None

    if settings.PATH_CERTIFICATE and settings.CERTIFICATE_SELF_SIGNED:
        certificate = open(settings.PATH_CERTIFICATE, 'r')

    bot.remove_webhook()

    return bot.set_webhook(get_webhook_url(), certificate)


def handle_request(request: HttpRequest):
    """Обрабатывает обращения к URL для Webhook.

    :param request:

    """
    if not request.body:
        LOGGER.debug('No data supplied.')
        return

    update = telebot.types.Update.de_json(request.body.decode('utf8'))

    message = update.message
    inline_query = update.inline_query

    if message:
        LOGGER.debug('Got simple message.')
        bot.process_new_messages([update.message])

    elif inline_query:
        LOGGER.debug('Got inline message.')
        bot.process_new_inline_query([inline_query])


@bot.message_handler(commands=['start'])
def on_start(message: Message):
    """Ответ на команду /start.

    :param message:

    """
    LOGGER.debug('Got /start command.')
    bot.reply_to(
        message, f'Рад знакомству, {message.from_user.first_name}.\nЧтобы получить справку, наберите команду /help.')


@bot.message_handler(commands=['chat_id'])
def on_chat_id(message: Message):
    """Ответ на команду /chat_id.

    :param message:

    """
    LOGGER.debug('Got /chat_id command.')
    bot.reply_to(message, f'Идентификатор этого чата: {message.chat.id}')


@bot.message_handler(commands=['help'])
def on_help(message: Message):
    """Ответ на команду /help.

    :param message:

    """
    LOGGER.debug('Got /help command.')
    bot.reply_to(
        message,
        'Я рассылаю новости сайта pythonz.net на канале https://telegram.me/pythonz.\n'
        'Кроме этого, вы можете вызвать меня в любом чате, чтобы получить ссылку на статью справочника.\n'
        'Пример: @pythonz_bot split')


@lru_cache(maxsize=2)
def get_inline_zen() -> List:
    """Возвращает список цитат из дзена питона."""
    results = []

    for idx, (zen_en, zen_ru) in enumerate(ZEN, 1):
        zen_en = clean(zen_en, tags=[], strip=True)
        zen_ru = clean(zen_ru, tags=[], strip=True)
        results.append(
            telebot.types.InlineQueryResultArticle(
                f'zen{idx}',
                f'{idx}. {zen_ru}',
                telebot.types.InputTextMessageContent(f'{idx}. {zen_en} — {zen_ru}'),
                description=zen_en
            ))

    return results


def compose_entities_inline_result(entities: List[Union['RealmBaseModel', 'CommonEntityModel']]) -> List:
    """Возвращает список сущностей для вывода в качестве встрочных результатов поиска ботом.

    :param entities:

    """
    results = []

    for entity in entities:

        title = str(entity)
        # Усечение чтобы уложиться в 64 Кб на одно сообщение
        # иначе, по словам техподдержки, получаем HTTP 414 Request-URI Too Large
        description = truncate_chars(entity.description, 30)

        results.append(
            telebot.types.InlineQueryResultArticle(
                str(entity.id),
                title,
                telebot.types.InputTextMessageContent(f'{title} — {entity.get_absolute_url(with_prefix=True)}'),
                description=description
            ))

    return results


@lru_cache(maxsize=64)
def get_inline_reference(term: str, items_limit: int = 25) -> List:
    """Возвращает статьи справочника.

    :param term: Текст запроса
    :param items_limit: Максимальное кол-во элементов для получения.

    """
    return compose_entities_inline_result(Reference.find(term[:200])[:items_limit])


@lru_cache(maxsize=20)
def get_inline_pep(term: str, items_limit: int = 10) -> List:
    """Возвращает ссылки на PEP.

    :param term: Текст запроса
    :param items_limit: Максимальное кол-во элементов для получения.

    """
    return compose_entities_inline_result(PEP.find(term[:200])[:items_limit])


@lru_cache(maxsize=2)
def get_inline_no_query() -> List:
    """Возвращает ответ на пустую строку запроса."""
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton('Бота в другой чат', switch_inline_query=''))
    markup.row(
        InlineKeyboardButton('Дзен', switch_inline_query_current_chat='zen '),
        InlineKeyboardButton('Поиск PEP', switch_inline_query_current_chat='pep '),
    )
    markup.row(
        InlineKeyboardButton('На pythonz.net', url='http://pythonz.net/'),
    )

    results = [
        telebot.types.InlineQueryResultArticle(
            'index',
            'Пульт управления роботом',
            telebot.types.InputTextMessageContent(
                'Нажимайте на кнопки, расположенные ниже, — получайте результат.'),
            description='Нажмите сюда, чтобы вызвать пульт.',
            reply_markup=markup,
        )
    ]
    return results


@bot.inline_handler(lambda query: True)
def query_text(inline_query: InlineQuery):
    """Ответ на запрос при вызове бота из чатов.

    :param inline_query:

    """
    term = inline_query.query.strip()

    if term:
        if term.startswith('zen'):
            results = get_inline_zen()

        elif term.startswith('pep'):
            results = get_inline_pep(term.strip('pep').strip())

        else:
            results = get_inline_reference(term)

    else:
        results = get_inline_no_query()

    LOGGER.debug('Answering inline.')
    bot.answer_inline_query(inline_query.id, results)


#@bot.message_handler(func=lambda message: True)
def echo_message(message: Message):
    """Ответ на неподдерживаемое сообщение.

    :param message:

    """
    LOGGER.debug('Got unhandled message.')
    bot.reply_to(message, f'{message.text}? Не знаю, что вам на это ответить.')
