import re
import logging
from datetime import timedelta
from collections import OrderedDict
from textwrap import wrap
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlparse, urlencode, urlunparse

from bleach import clean
from django.contrib import messages
from django.utils import timezone
from django.utils.text import Truncator


def get_logger(name):
    """Возвращает объект-журналёр для использования в модулях.

    :param name:
    :rtype: logging.Logger
    """
    return logging.getLogger('pythonz.%s' % name)


LOG = get_logger(__name__)


def get_datetime_from_till(days_gap):
    """Возвращает даты "с" и "по", где "по" - текущая дата,
    а "с" отстоит от неё в прошлое на указанное количество дней.

    :param int days_gap:
    :rtype: tuple
    """
    date_till = timezone.now()
    date_from = date_till - timedelta(days=days_gap)
    return date_from, date_till


class PersonName(object):
    """Предоставляет инструменты для представления имени персоны в разном виде."""

    __slots__ = ['_name', 'is_valid']

    def __init__(self, name):
        name = re.sub('\s+', ' ', name).strip()

        self._name = name.split(' ')

        self.is_valid = len(self._name) > 1
        """Флаг, указывающие на то, что имя состоит хотя бы из двух частей (имя и фамилия).

        :type: bool
        """

        if not self.is_valid:
            self._name = ['', '']

    def get_variants(self):
        """Возвращает наиболее часто встречающиеся варианты представления имени.

        :rtype: str
        """
        variants = []
        other = [self.full, self.short, self.first_last, self.last_first]

        for variant in other:
            if variant and variant not in variants:
                variants.append(variant)

        return variants

    @property
    def last_first(self):
        """Фамилия и имя (отчество/второе имя исключаются).

        :rtype: str
        """
        return ('%s %s' % (self._name[-1], self._name[0])).strip()

    @property
    def first_last(self):
        """Имя и фамилия (отчество/второе имя исключаются).

        :rtype: str
        """
        return ('%s %s' % (self._name[0], self._name[-1])).strip()

    @property
    def first(self):
        """Имя.

        :rtype: str
        """
        return self._name[0].strip()

    @property
    def last(self):
        """Фамилия.

        :rtype: str
        """
        return self._name[-1].strip()

    @property
    def full(self):
        """Имя, отчество, фамилия.

        :rtype: str
        """
        return ' '.join(self._name).strip()

    @property
    def short(self):
        """Возвращает инициал имени и фамилию.

        :param str name:
        :rtype: str
        """
        if not self.is_valid:
            return ''

        name = self._name
        short = '%s. %s' % (name[0][0], ' '.join(name[1:]))
        return short


def truncate_chars(text, to, html=False):
    """Укорачивает поданный на вход текст до опционально указанного количества символов."""
    return Truncator(text).chars(to, html=html)


def truncate_words(text, to, html=False):
    """Укорачивает поданный на вход текст до опционально указанного количества слов."""
    return Truncator(text).words(to, html=html)


def format_currency(val):
    """Форматирует значение валюты, разбивая его кратно
    тысяче для облегчения восприятия.

    :param val:
    :return:
    """
    return ' '.join(wrap(str(int(val))[::-1], 3))[::-1]


def sync_many_to_many(src_obj, model, m2m_attr, related_attr, known_items, unknown_handler=None):
    """Синхронизирует (при необходимости) список из указанного атрибута
    объекта-источника в поле многие-ко-многим указанной модели.

    Возвращает список неизвестных (отсутствующих в known_items) элементов из src_obj.m2m_attr,
    либо созданных при помощи unknown_handler.

    Внимание: для правильной работы необходимо, чтобы в БД уже был и объект model и объекты из known_items.

    :param object src_obj: Объект-источник, в котором есть src_obj.m2m_attr, содержащий
        список (например строк), которым будут сопоставлены объекты из known_items.
        Либо может быть указан список напрямую.

    :param Model model: Модель, поле которой требуется обновить при необходимости.

    :param str m2m_attr: Имя атрибута модели, являющегося полем многие-ко-многим.

    :param str related_attr: Имя атрибута, в объектах многие-ко-многим, считающееся ключевым.
        Значения из этого атрибута ожидаются в списке из src_obj.m2m_attr.

    :param dict known_items: Ключи - это значения из src_obj.m2m_attr,
        а значения - это модель из отношения многие-ко-многим, либо список моделей.

    :param callable unknown_handler: Функция-обработчик для неизвестных элементов,
        создающая объект налету. Должна принимать элемент списка src_obj.m2m_attr,
        по которому будет создан объект, а также словарь known_items, который следует
        дополнить созданным объектом.

    :rtype: list
    """
    if isinstance(src_obj, list):
        new_list = src_obj
    else:
        new_list = getattr(src_obj, m2m_attr)

    if not new_list:
        return

    m2m_model_attr = getattr(model, m2m_attr)
    old_many = {m2m_model_attr.values_list(related_attr, flat=True)}

    unknown = []
    unknown_handler = unknown_handler or (lambda item, known_items: None)

    if old_many != set(new_list):
        # Данные двух наборов (хранящегося в БД и полученнго) не совпадают.
        # Синхронизируем данные в БД.
        m2m_model_attr.clear()
        to_add = []
        for item in new_list:

            if isinstance(item, str):
                item = item.strip()

            if not item:
                continue

            val = known_items.get(item, None)  # Модель или список моделей.

            if val is None:
                LOG.debug('Handling unknown item in sync_many_to_many(): %s', item)
                val = unknown_handler(item, known_items)
                if val is None:
                    unknown.append(item)
                    continue

            if not isinstance(val, list):
                val = [val]

            for item in val:
                to_add.append(item)

        m2m_model_attr.add(*to_add)

    return unknown


def update_url_qs(url, new_qs_params):
    """Дополняет указанный URL указанными параметрами запроса,
    при этом заменяя значения уже имеющихся одноимённых параметров, если
    таковые были в URL изначально

    :param str url:
    :param dict new_qs_params:
    :rtype: str
    """
    parsed = list(urlparse(url))
    parsed_qs = parse_qs(parsed[4])
    parsed_qs.update(new_qs_params)
    parsed[4] = urlencode(parsed_qs, doseq=True)
    return urlunparse(parsed)


class UTM:
    """Утилиты для работы с UTM (Urchin Tracking Module) метками."""

    @classmethod
    def add_to_url(cls, url, source, medium, campaign):
        """Добавляет UTM метки в указаный URL.

        :param url:

        :param source: Название источника перехода.
            Например, pythonz, google.

        :param medium: Рекламный канал.
            Например referral, cpc, banner, email

        :param campaign: Ключевое слово (название компании).
            Например слоган продукта, промокод.

        :rtype: str
        """
        params = {
            'utm_source': source,
            'utm_medium': medium,
            'utm_campaign': campaign,
        }
        return update_url_qs(url, params)

    @classmethod
    def add_to_external_url(cls, url):
        """Добавляет UTM метки в указанный внешний URL.

        :param str url:
        :rtype: str
        """
        return cls.add_to_url(url, 'pythonz', 'referral', 'item')

    @classmethod
    def add_to_internal_url(cls, url, source):
        """Добавляет UTM метки в указанный внутренний URL.

        :param str url:
        :param str source:
        :rtype: str
        """
        return cls.add_to_url(url, source, 'link', 'promo')


class BasicTypograph:
    """Содержит базовые правила типографики.
    Позволяет применить эти правила к строке.

    """

    rules = OrderedDict((
        ('QUOTES_REPLACE', (re.compile('(„|“|”|(\'\'))'), '"')),
        ('DASH_REPLACE', (re.compile('(-|­|–|—|―|−|--)'), '-')),

        ('SEQUENTIAL_SPACES', (re.compile('([ \t]+)'), ' ')),

        ('DASH_EM', (re.compile('([ ,])-[ ]'), '\g<1>— ')),
        ('DASH_EN', (re.compile('(\d+)[ ]*-[ ]*(\d+)'), '\g<1>–\g<2>')),

        ('HELLIP', (re.compile('\.{2,3}'), '…')),
        ('COPYRIGHT', (re.compile('\((c|с)\)'), '©')),
        ('TRADEMARK', (re.compile('\(tm\)'), '™')),
        ('TRADEMARK_R', (re.compile('\(r\)'), '®')),

        ('QUOTES_CYR_CLOSE', (re.compile('(\S+)"', re.U), '\g<1>»')),
        ('QUOTES_CYR_OPEN', (re.compile('"(\S+)', re.U), '«\g<1>')),
    ))

    @classmethod
    def apply_to(cls, input_str):
        input_str = ' %s ' % input_str.strip()

        for name, (regexp, replacement) in cls.rules.items():
            input_str = re.sub(regexp, replacement, input_str)

        return input_str.strip()


class TextCompiler:
    """Предоставляет инструменты для RST-подобного форматирования в HTML."""

    RE_CODE = re.compile('\.{2}\s*code::([^\n]+)?\n{1,2}(.+?)\n{3}((?=\S)|$)', re.S)
    RE_TABLE = re.compile('\.{2}\s*table::([^\n]+)?\n{1,2}(.+?)\n{3}((?=\S)|$)', re.S)
    RE_NOTE = re.compile('\.{2}\s*note::\s*([^\n]+)\n', re.S)
    RE_TITLE = re.compile('\.{2}\s*title::\s*([^\n]+)\n', re.S)
    RE_WARNIGN = re.compile('\.{2}\s*warning::\s*([^\n]+)\n', re.S)
    RE_GIST = re.compile('\.{2}\s*gist::\s*([^\n]+)\n', re.S)
    RE_POLL = re.compile('\.{2}\s*poll::\s*([^\n]+)\n', re.S)
    RE_PODSTER = re.compile('\.{2}\s*podster::\s*([^\n]+)[/]*\n', re.S)
    RE_IMAGE = re.compile('\.{2}\s*image::\s*([^\n]+)[/]*\n', re.S)
    RE_ACCENT = re.compile('`{2}([^`\n]+)`{2}')
    RE_QUOTE = re.compile('`{3}\n+([^`]+)\n+`{3}')
    RE_BOLD = re.compile('\*{2}([^\s]{1}[^*\n]+[^\s]{1})\*{2}')
    RE_ITALIC = re.compile('\*([^\s]{1}[^*\n]+[^\s]{1})\*')
    RE_URL = re.compile('(?<!["])(http[s]?:[^\s\)\<]+)')
    RE_URL_WITH_TITLE = re.compile('`([^\◀]+)\n*\◀([^\▶]+)\▶`_', re.U)
    RE_UL = re.compile('^\*\s+([^\n]+)\n', re.M)

    @classmethod
    def compile(cls, text):
        """Преобразует rst-подобное форматичрование в html.

        :param text:
        :return:
        """
        def replace_href(match):
            return '<a href="%s">%s</a>' % (match.group(1), url_mangle(match.group(1)))

        def replace_code(match):
            lang = match.group(1)
            code = match.group(2)
            return '<pre><code class="%s">%s</code></pre>\n' % ((lang or 'python').strip(), code)

        def replace_table(match):
            opt = match.group(1)  # Зарезервированная опция.
            body = match.group(2)
            rows = []

            bg_map = {
                'i': 'info',
                's': 'success',
                'w': 'warning',
                'd': 'danger',
            }

            for line in body.splitlines():
                if line.startswith('! '):
                    # Заголовок таблицы.
                    rows.append(
                        '<thead><tr><th>%s</th></tr></thead>' %
                        '</th><th>'.join(line.lstrip(' !').split(' | ')))
                else:
                    attrs_row = ''
                    cells = []
                    for value in map(str.strip, line.split(' | ')):

                        attrs_cell = ''
                        # Подсветка. Например, !b:d+ для всего ряда или !b:d ячейки.
                        if value.startswith('!b:'):
                            bg_letter, row_sign = value[3:5]
                            value = value[5:].strip()

                            bg_class = bg_map.get(bg_letter, '')
                            if bg_class:
                                attr = ' class="%s"' % bg_class

                                if row_sign == '+':
                                    attrs_row = attr
                                else:
                                    attrs_cell = attr

                        cells.append('<td%s>%s</td>' % (attrs_cell, value))

                    rows.append('<tr%s>%s</tr>' % (attrs_row, ''.join(cells)))

            return (
                '<div class="table-responsive">'
                '<table class="table table-striped table-bordered table-hover">%s</table></div>\n' % ''.join(rows))

        # Заменяем некоторые символы для правила RE_URL_WITH_TITLE, чтобы их не устранил bleach.
        text = text.replace('<ht', '◀ht')
        text = text.replace('</', '◀/')
        text = text.replace('>`', '▶`')

        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

        text = clean(text)

        text = text.replace('\r\n', '\n')

        text = re.sub(cls.RE_UL, '<li>\g<1></li>', text)
        text = text.replace('\n<li>', '\n<ul><li>').replace('</li>\n', '</li></ul>\n')

        text = re.sub(cls.RE_BOLD, '<b>\g<1></b>', text)
        text = re.sub(cls.RE_ITALIC, '<i>\g<1></i>', text)
        text = re.sub(cls.RE_QUOTE, '<blockquote>\g<1></blockquote>', text)
        text = re.sub(cls.RE_ACCENT, '<code>\g<1></code>', text)
        text = re.sub(cls.RE_CODE, replace_code, text)
        text = re.sub(cls.RE_URL_WITH_TITLE, '<a href="\g<2>">\g<1></a>', text)
        text = re.sub(cls.RE_GIST, '<script src="https://gist.github.com/\g<1>.js"></script>', text)
        text = re.sub(cls.RE_POLL, '<script src="http://static.polldaddy.com/p/\g<1>.js"></script>', text)
        text = re.sub(cls.RE_TABLE, replace_table, text)

        text = re.sub(cls.RE_TITLE, '<h4 data-geopattern="\g<1>" class="subtitle">\g<1></h4>', text)

        text = re.sub(
            cls.RE_NOTE, '<div class="panel panel-primary"><div class="panel-heading">На заметку</div>'
                         '<div class="panel-body">\g<1></div></div>', text)
        text = re.sub(
            cls.RE_WARNIGN, '<div class="panel panel-danger"><div class="panel-heading">Внимание</div>'
                            '<div class="panel-body">\g<1></div></div>', text)

        text = re.sub(
            cls.RE_PODSTER,
            '<iframe width="100%" height="85" src="\g<1>/embed/13?link=1" frameborder="0" allowtransparency="true">'
            '</iframe>',
            text
        )
        text = re.sub(
            cls.RE_IMAGE, '<img alt="\g<1>" src="\g<1>" data-canonical-src="\g<1>" style="max-width:100%;">', text)
        text = re.sub(cls.RE_URL, replace_href, text)

        text = text.replace('\n', '<br>')
        return text


def url_mangle(url):
    """Усекает длинные URL практически до неузноваемости, делая нефункциональным, но коротким.
    Всё ради уменьшения длины строки.

    :param url:
    :return:
    """
    if len(url) <= 45:
        return url
    path, qs, frag = 2, 3, 4
    splitted = list(urlsplit(url))
    splitted[qs] = ''
    splitted[frag] = ''
    if splitted[path].strip('/'):
        splitted[path] = '<...>%s' % splitted[path].split('/')[-1]  # Последний кусок пути.
    mangled = urlunsplit(splitted)
    return mangled


def message_info(request, message):
    """Регистрирует сообщение информирующего типа для вывода пользователю на странице.

    :param Request request:
    :param str message:
    :return:
    """
    messages.add_message(request, messages.INFO, message, extra_tags='info')


def message_warning(request, message):
    """Регистрирует предупреждающее сообщение для вывода пользователю на странице.

    :param Request request:
    :param str message:
    :return:
    """
    messages.add_message(request, messages.WARNING, message, extra_tags='warning')


def message_success(request, message):
    """Регистрирует ободряющее сообщение для вывода пользователю на странице.

    :param Request request:
    :param str message:
    :return:
    """
    messages.add_message(request, messages.SUCCESS, message, extra_tags='success')


def message_error(request, message):
    """Регистрирует сообщение об ошибке для вывода пользователю на странице.

    :param Request request:
    :param str message:
    :return:
    """
    messages.add_message(request, messages.ERROR, message, extra_tags='danger')


TRANSLATION_DICT = str.maketrans(
    "ёЁ!\"№;%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,",
    "`~!@#$%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
)

RE_NON_ASCII = re.compile('[^\x00-\x7F]')


def swap_layout(src_text):
    """Заменяет кириллические символы строки на латинские в соответствии
    с классической раскладкой клавиатуры, если строка не содержит символов кириллицы,
    то возвращатся пустая строка, символизируя, что трансляция не производилась.

    :param str src_text:
    :rtype: str
    """
    if not RE_NON_ASCII.match(src_text):
        return ''

    return src_text.translate(TRANSLATION_DICT)
