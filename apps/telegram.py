from functools import lru_cache

import telebot
from bleach import clean
from django.conf import settings

from .models import Reference
from .zen import ZEN


bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)


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
        return

    update = telebot.types.Update.de_json(request.body.decode('utf8'))

    message = update.message
    inline_query = update.inline_query

    if message:
        bot.process_new_messages([update.message])

    elif inline_query:
        bot.process_new_inline_query([inline_query])


@bot.message_handler(commands=['start'])
def on_start(message):
    """Ответ на команду /start.

    :param telebot.types.Message message:
    """
    bot.reply_to(
        message, 'Рад знакомству, %s.\nЧтобы получить справку, наберите команду /help.' % message.from_user.first_name)


@bot.message_handler(commands=['help'])
def on_start(message):
    """Ответ на команду /help.

    :param telebot.types.Message message:
    """
    bot.reply_to(
        message,
        'Я рассылаю новости сайта pythonz.net на канале https://telegram.me/pythonz.\n'
        'Кроме этого, вы можете вызвать меня в любом чате, чтобы получить ссылку на статью справочника.\n'
        'Примеры:\n'
        '@pythonz_bot str.\n'
        '@pythonz_bot import this')


@lru_cache(maxsize=2)
def get_zen_inlines():
    """Возвращает список цитат из дзена питона."""
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


@bot.inline_handler(lambda query: True)
def query_text(inline_query):
    """Ответ на запрос при вызове бота из чатов.

    :param telebot.types.InlineQuery inline_query:
    """
    term = inline_query.query.strip()
    results = []

    if term:
        if term == 'import this':

           results = get_zen_inlines()

        else:

            found_items = Reference.objects.filter(title__icontains=term)

            for item in found_items:
                title = item.title
                description = item.description
                results.append(
                    telebot.types.InlineQueryResultArticle(
                        id=str(item.id),
                        title=title,
                        message_text='%s — %s %s' % (title, description, item.get_absolute_url(True, 'telesearch')),
                        description=description,
                        disable_web_page_preview=True,
                    ))

    else:
        results.append(
            telebot.types.InlineQueryResultArticle(
                id='index',
                title='pythonz.net',
                message_text='http://pythonz.net',
                description='Про Python',
            ))

    bot.answer_inline_query(inline_query.id, results)


@bot.message_handler(func=lambda message: True)
def echo_message(message):
    """Ответ на неподдерживаемое сообщение.

    :param telebot.types.Message message:
    """
    bot.reply_to(message, '%s? Не знаю, что вам на это ответить.' % message.text)
