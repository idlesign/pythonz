from functools import lru_cache

import telebot
from telebot.apihelper import _convert_inline_results, _make_request
from bleach import clean
from django.conf import settings

from .utils import truncate_chars
from .models import Reference
from .zen import ZEN
from .logger import get_logger


LOGGER = get_logger('telebot')


# Перекрыта до выпуска версии с https://github.com/eternnoir/pyTelegramBotAPI/pull/116
def answer_inline_query_patched(token, inline_query_id, results, cache_time=None, is_personal=None, next_offset=None):
    method_url = 'answerInlineQuery'
    payload = {'inline_query_id': inline_query_id, 'results': _convert_inline_results(results)}
    if cache_time:
        payload['cache_time'] = cache_time
    if is_personal:
        payload['is_personal'] = is_personal
    if next_offset:
        payload['next_offset'] = next_offset
    return _make_request(token, method_url, params=payload, method='post')


# Перекрыт до выпуска версии с https://github.com/eternnoir/pyTelegramBotAPI/pull/116
class TeleBotPatched(telebot.TeleBot):

    def answer_inline_query(self, inline_query_id, results, cache_time=None, is_personal=None, next_offset=None):
        return answer_inline_query_patched(self.token, inline_query_id, results, cache_time, is_personal, next_offset)


bot = TeleBotPatched(settings.TELEGRAM_BOT_TOKEN, threaded=False)


def get_webhook_url():
    """Возвращает webhook URL."""
    return '%s/%s/' % (settings.SITE_URL.replace('http', 'https'), settings.TELEGRAM_BOT_URL)


def set_webhook():
    """Конфигурирует механизм webhook."""
    certificate = None
    if settings.PATH_CERTIFICATE and settings.CERTIFICATE_SELF_SIGNED:
        certificate = open(settings.PATH_CERTIFICATE, 'r')

    bot.remove_webhook()
    return bot.set_webhook(get_webhook_url(), certificate)


def handle_request(request):
    """Обрабатывает обращения к URL для Webhook.

    :param Request request:
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
def on_start(message):
    """Ответ на команду /start.

    :param telebot.types.Message message:
    """
    LOGGER.debug('Got /start command.')
    bot.reply_to(
        message, 'Рад знакомству, %s.\nЧтобы получить справку, наберите команду /help.' % message.from_user.first_name)


@bot.message_handler(commands=['chat_id'])
def on_start(message):
    """Ответ на команду /chat_id.

    :param telebot.types.Message message:
    """
    LOGGER.debug('Got /chat_id command.')
    bot.reply_to(message, 'Идентификатор этого чата: ' % message.chat.id)


@bot.message_handler(commands=['help'])
def on_help(message):
    """Ответ на команду /help.

    :param telebot.types.Message message:
    """
    LOGGER.debug('Got /help command.')
    bot.reply_to(
        message,
        'Я рассылаю новости сайта pythonz.net на канале https://telegram.me/pythonz.\n'
        'Кроме этого, вы можете вызвать меня в любом чате, чтобы получить ссылку на статью справочника.\n'
        'Пример: @pythonz_bot split')


@lru_cache(maxsize=2)
def get_inline_zen():
    """Возвращает список цитат из дзена питона.

    :rtype: list
    """
    results = []

    for idx, (zen_en, zen_ru) in enumerate(ZEN, 1):
        zen_en = clean(zen_en, tags=[], strip=True)
        zen_ru = clean(zen_ru, tags=[], strip=True)
        results.append(
            telebot.types.InlineQueryResultArticle(
                id='zen%s' % idx,
                title='%s. %s' % (idx, zen_ru),
                message_text='%s. %s — %s' % (idx, zen_en, zen_ru),
                description=zen_en
            ))

    return results


@lru_cache(maxsize=64)
def get_inline_reference(term, items_limit=25):
    """Возвращает статьи справочника.

    :param str term: Текст запроса
    :param int items_limit: Максимальное кол-во элементов для получения.
    :rtype: list
    """
    results = []
    found_items = Reference.find(term)[:items_limit]

    for item in found_items:
        title = item.title
        # Усечение чтобы уложиться в 64 Кб на одно сообщение
        # иначе, по словам техподдержки, получаем HTTP 414 Request-URI Too Large
        description = truncate_chars(item.description, 30)
        results.append(
            telebot.types.InlineQueryResultArticle(
                id=str(item.id),
                title=title,
                message_text='%s — %s' % (title, item.get_absolute_url(True, 'telesearch')),
                description=description
            ))
    return results


@lru_cache(maxsize=2)
def get_inline_no_query():
    """Возвращает ответ на пустую строку запроса.

    :rtype: list
    """
    results = [
        telebot.types.InlineQueryResultArticle(
            id='index',
            title='pythonz.net',
            message_text='http://pythonz.net',
            description='Про Python',
        )
    ]
    return results


@bot.inline_handler(lambda query: True)
def query_text(inline_query):
    """Ответ на запрос при вызове бота из чатов.

    :param telebot.types.InlineQuery inline_query:
    """
    term = inline_query.query.strip()

    if term:
        results = get_inline_reference(term)

    else:
        results = get_inline_zen()

    LOGGER.debug('Answering inline.')
    bot.answer_inline_query(inline_query.id, results)


@bot.message_handler(func=lambda message: True)
def echo_message(message):
    """Ответ на неподдерживаемое сообщение.

    :param telebot.types.Message message:
    """
    LOGGER.debug('Got unhandled message.')
    bot.reply_to(message, '%s? Не знаю, что вам на это ответить.' % message.text)
