import logging
import re
from datetime import timedelta, datetime
from textwrap import wrap
from typing import Tuple, List, Dict, Callable, Any, Union
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlparse, urlencode, urlunparse

from bleach import clean
from django.contrib import messages
from django.db.models import Model
from django.http import HttpRequest
from django.utils import timezone
from django.utils.text import Truncator

from .exceptions import RemoteSourceError
from .integration.videos import VideoBroker


def get_logger(name: str) -> logging.Logger:
    """Возвращает объект-журналёр для использования в модулях.

    :param name:

    """
    return logging.getLogger(f'pythonz.{name}')


LOG = get_logger(__name__)


def get_datetime_from_till(days_gap: int) -> Tuple[datetime, datetime]:
    """Возвращает даты "с" и "по", где "по" - текущая дата,
    а "с" отстоит от неё в прошлое на указанное количество дней.

    :param int days_gap:

    """
    date_till = timezone.now()
    date_from = date_till - timedelta(days=days_gap)

    return date_from, date_till


class PersonName:
    """Предоставляет инструменты для представления имени персоны в разном виде."""

    __slots__ = ['_name', 'is_valid']

    def __init__(self, name: str):
        name = re.sub(r'\s+', ' ', name).strip()

        self._name: List[str] = name.split(' ')

        self.is_valid: bool = len(self._name) > 1
        """Флаг, указывающие на то, что имя состоит хотя бы из двух частей (имя и фамилия)."""

        if not self.is_valid:
            self._name = ['', '']

    @property
    def get_variants(self) -> List[str]:
        """Возвращает наиболее часто встречающиеся варианты представления имени."""
        variants = []
        other = [self.full, self.short, self.first_last, self.last_first]

        for variant in other:
            if variant and variant not in variants:
                variants.append(variant)

        return variants

    @property
    def last_first(self) -> str:
        """Фамилия и имя (отчество/второе имя исключаются)."""
        return f'{self._name[-1]} {self._name[0]}'.strip()

    @property
    def first_last(self) -> str:
        """Имя и фамилия (отчество/второе имя исключаются)."""
        return f'{self._name[0]} {self._name[-1]}'.strip()

    @property
    def first(self) -> str:
        """Имя."""
        return self._name[0].strip()

    @property
    def last(self) -> str:
        """Фамилия."""
        return self._name[-1].strip()

    @property
    def full(self) -> str:
        """Имя, отчество, фамилия."""
        return ' '.join(self._name).strip()

    @property
    def short(self) -> str:
        """Возвращает инициал имени и фамилию."""

        if not self.is_valid:
            return ''

        name = self._name

        return f"{name[0][0]}. {' '.join(name[1:])}"


def truncate_chars(text: str, to: int, html: bool = False) -> str:
    """Укорачивает поданный на вход текст до опционально указанного количества символов."""
    return Truncator(text).chars(to, html=html)


def truncate_words(text: str, to: int, html: bool = False) -> str:
    """Укорачивает поданный на вход текст до опционально указанного количества слов."""
    return Truncator(text).words(to, html=html)


def format_currency(val: int) -> str:
    """Форматирует значение валюты, разбивая его кратно
    тысяче для облегчения восприятия.

    :param val:

    """
    return ' '.join(wrap(str(int(val))[::-1], 3))[::-1]


def sync_many_to_many(
    src_obj: Any,
    model: Model,
    m2m_attr: str,
    related_attr: str,
    known_items: Dict[str, Union[Model, List[Model]]],
    unknown_handler: Callable = None
) -> List[str]:
    """Синхронизирует (при необходимости) список из указанного атрибута
    объекта-источника в поле многие-ко-многим указанной модели.

    Возвращает список неизвестных (отсутствующих в known_items) элементов из src_obj.m2m_attr,
    либо созданных при помощи unknown_handler.

    Внимание: для правильной работы необходимо, чтобы в БД уже был и объект model и объекты из known_items.

    :param src_obj: Объект-источник, в котором есть src_obj.m2m_attr, содержащий
        список (например строк), которым будут сопоставлены объекты из known_items.
        Либо может быть указан список напрямую.

    :param model: Модель, поле которой требуется обновить при необходимости.

    :param m2m_attr: Имя атрибута модели, являющегося полем многие-ко-многим.

    :param related_attr: Имя атрибута, в объектах многие-ко-многим, считающееся ключевым.
        Значения из этого атрибута ожидаются в списке из src_obj.m2m_attr.

    :param known_items: Ключи - это значения из src_obj.m2m_attr,
        а значения - это модель из отношения многие-ко-многим, либо список моделей.

    :param unknown_handler: Функция-обработчик для неизвестных элементов,
        создающая объект налету. Должна принимать элемент списка src_obj.m2m_attr,
        по которому будет создан объект, а также словарь known_items, который следует
        дополнить созданным объектом.

    """
    if isinstance(src_obj, list):
        new_list = src_obj

    else:
        new_list = getattr(src_obj, m2m_attr)

    if not new_list:
        return []

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

                LOG.debug(f'Handling unknown item in sync_many_to_many(): {item}')
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


def update_url_qs(url: str, new_qs_params: dict) -> str:
    """Дополняет указанный URL указанными параметрами запроса,
    при этом заменяя значения уже имеющихся одноимённых параметров, если
    таковые были в URL изначально

    :param url:
    :param new_qs_params:

    """
    parsed = list(urlparse(url))

    parsed_qs = parse_qs(parsed[4])
    parsed_qs.update(new_qs_params)
    parsed[4] = urlencode(parsed_qs, doseq=True)

    return urlunparse(parsed)


class UTM:
    """Утилиты для работы с UTM (Urchin Tracking Module) метками."""

    @classmethod
    def add_to_url(cls, url: str, source: str, medium: str, campaign: str) -> str:
        """Добавляет UTM метки в указаный URL.

        :param url:

        :param source: Название источника перехода.
            Например, pythonz, google.

        :param medium: Рекламный канал.
            Например referral, cpc, banner, email

        :param campaign: Ключевое слово (название компании).
            Например слоган продукта, промокод.

        """
        params = {
            'utm_source': source,
            'utm_medium': medium,
            'utm_campaign': campaign,
        }

        return update_url_qs(url, params)

    @classmethod
    def add_to_external_url(cls, url: str) -> str:
        """Добавляет UTM метки в указанный внешний URL.

        :param url:

        """
        return cls.add_to_url(url, 'pythonz', 'referral', 'item')

    @classmethod
    def add_to_internal_url(cls, url: str, source: str) -> str:
        """Добавляет UTM метки в указанный внутренний URL.

        :param url:
        :param source:

        """
        return cls.add_to_url(url, source, 'link', 'promo')


class BasicTypograph:
    """Содержит базовые правила типографики.
    Позволяет применить эти правила к строке.

    """
    rules = {
        'QUOTES_REPLACE': (re.compile('(„|“|”|(\'\'))'), '"'),
        'DASH_REPLACE': (re.compile('(-|­|–|—|―|−|--)'), '-'),

        'SEQUENTIAL_SPACES': (re.compile('([ \t]+)'), ' '),

        'DASH_EM': (re.compile('([ ,])-[ ]'), '\g<1>— '),
        'DASH_EN': (re.compile('(\d+)[ ]*-[ ]*(\d+)'), '\g<1>–\g<2>'),

        'HELLIP': (re.compile('\.{2,3}'), '…'),
        'COPYRIGHT': (re.compile('\((c|с)\)'), '©'),
        'TRADEMARK': (re.compile('\(tm\)'), '™'),
        'TRADEMARK_R': (re.compile('\(r\)'), '®'),

        'QUOTES_CYR_CLOSE': (re.compile('(\S+)"', re.U), '\g<1>»'),
        'QUOTES_CYR_OPEN': (re.compile('"(\S+)', re.U), '«\g<1>'),
    }

    @classmethod
    def apply_to(cls, input_str: str) -> str:

        input_str = f' {input_str.strip()} '

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
    RE_VIDEO = re.compile('\.{2}\s*video::\s*([^\n]+)\n', re.S)
    RE_PODSTER = re.compile('\.{2}\s*podster::\s*([^\n]+)[/]*\n', re.S)
    RE_IMAGE = re.compile('\.{2}\s*image::\s*([^\n]+)[/]*\n', re.S)
    RE_ACCENT = re.compile('`{2}([^`\n]+)`{2}')
    RE_QUOTE = re.compile('`{3}\n+([^`]+)\n+`{3}')
    RE_BOLD = re.compile('\*{2}([^\s]{1}[^*\n]+([^\s]{1})?)\*{2}')
    RE_ITALIC = re.compile('\*([^\s]{1}[^*\n]+[^\s]{1})\*')
    RE_URL = re.compile('(?<!["])(http[s]?:[^\s\)\<]+)')
    RE_URL_WITH_TITLE = re.compile('`([^\◀]+)\n*\◀([^\▶]+)\▶`_', re.U)
    RE_UL = re.compile('^\*\s+([^\n]+)\n', re.M)

    @classmethod
    def compile(cls, text: str) -> str:
        """Преобразует rst-подобное форматичрование в html.

        :param text:

        """
        def replace_href(match):
            return f'<a href="{match.group(1)}">{url_mangle(match.group(1))}</a>'

        def replace_code(match):
            lang = (match.group(1) or 'python').strip()
            code = match.group(2)
            return f'<pre><code class="{lang}">{code}</code></pre>\n'

        def replace_video(match):

            try:
                code, _ = VideoBroker.get_code_and_cover(match.group(1), wrap_responsive=True)

            except RemoteSourceError:
                code = '<b>Ошибка встраивания видео: неподдерживаемый сервис.</b>'

            return code

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
                        f"<thead><tr><th>{'</th><th>'.join(line.lstrip(' !').split(' | '))}</th></tr></thead>")
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
                                attr = f' class="{bg_class}"'

                                if row_sign == '+':
                                    attrs_row = attr
                                else:
                                    attrs_cell = attr

                        cells.append(f'<td{attrs_cell}>{value}</td>')

                    rows.append(f"<tr{attrs_row}>{''.join(cells)}</tr>")

            rows = ''.join(rows)

            return (
                '<div class="table-responsive"><table class="table table-striped table-bordered table-hover">'
                f'{rows}</table></div>\n')

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

        text = re.sub(
            cls.RE_POLL,
            '<div class="card bg-light p-2 m-2"><div class="card-body">'
            '<script src="https://yastatic.net/q/forms-frontend-ext/_/embed.js"></script>'
            '<iframe src="https://forms.yandex.ru/u/\g<1>/?iframe=1" frameborder="0" width="100%" name="ya-form-\g<1>">'
            '</iframe></div></div>',
            text)

        text = re.sub(cls.RE_VIDEO, replace_video, text)

        text = re.sub(cls.RE_TABLE, replace_table, text)

        text = re.sub(cls.RE_TITLE, '<h4 data-geopattern="\g<1>" class="subtitle">\g<1></h4>', text)

        text = re.sub(
            cls.RE_NOTE, '<div class="card mb-3"><div class="card-header text-white bg-success">На заметку</div>'
                         '<div class="card-body">\g<1></div></div>', text)
        text = re.sub(
            cls.RE_WARNIGN, '<div class="card mb-3"><div class="card-header text-white bg-danger">Внимание</div>'
                            '<div class="card-body">\g<1></div></div>', text)

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


def url_mangle(url: str) -> str:
    """Усекает длинные URL практически до неузноваемости, делая нефункциональным, но коротким.
    Всё ради уменьшения длины строки.

    :param url:

    """
    if len(url) <= 45:
        return url

    path, qs, frag = 2, 3, 4
    splitted = list(urlsplit(url))
    splitted[qs] = ''
    splitted[frag] = ''

    if splitted[path].strip('/'):
        splitted[path] = f"<...>{splitted[path].split('/')[-1]}"  # Последний кусок пути.

    mangled = urlunsplit(splitted)

    return mangled


def message_info(request: HttpRequest, message: str):
    """Регистрирует сообщение информирующего типа для вывода пользователю на странице.

    :param request:
    :param message:

    """
    messages.add_message(request, messages.INFO, message, extra_tags='info')


def message_warning(request: HttpRequest, message: str):
    """Регистрирует предупреждающее сообщение для вывода пользователю на странице.

    :param request:
    :param message:

    """
    messages.add_message(request, messages.WARNING, message, extra_tags='warning')


def message_success(request: HttpRequest, message: str):
    """Регистрирует ободряющее сообщение для вывода пользователю на странице.

    :param request:
    :param message:

    """
    messages.add_message(request, messages.SUCCESS, message, extra_tags='success')


def message_error(request: HttpRequest, message: str):
    """Регистрирует сообщение об ошибке для вывода пользователю на странице.

    :param request:
    :param message:

    """
    messages.add_message(request, messages.ERROR, message, extra_tags='danger')


TRANSLATION_DICT = str.maketrans(
    "ёЁ!\"№;%:?йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,",
    "`~!@#$%^&qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
)

RE_NON_ASCII = re.compile('[^\x00-\x7F]')


def swap_layout(src_text: str) -> str:
    """Заменяет кириллические символы строки на латинские в соответствии
    с классической раскладкой клавиатуры, если строка не содержит символов кириллицы,
    то возвращатся пустая строка, символизируя, что трансляция не производилась.

    :param src_text:

    """
    if not RE_NON_ASCII.match(src_text):
        return ''

    return src_text.translate(TRANSLATION_DICT)
