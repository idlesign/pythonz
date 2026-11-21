import logging
import re
from collections.abc import Callable
from datetime import datetime, timedelta
from textwrap import wrap
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlsplit, urlunparse, urlunsplit

from django.contrib import messages
from django.db import models
from django.db.models import Model
from django.http import HttpRequest
from django.utils import timezone
from django.utils.text import Truncator


def get_logger(name: str) -> logging.Logger:
    """Возвращает объект-журналёр для использования в модулях.

    :param name:

    """
    return logging.getLogger(f'pythonz.{name}')


LOG = get_logger(__name__)


def get_datetime_from_till(days_gap: int) -> tuple[datetime, datetime]:
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

        self._name: list[str] = name.split(' ')

        self.is_valid: bool = len(self._name) > 1
        """Флаг, указывающие на то, что имя состоит хотя бы из двух частей (имя и фамилия)."""

        if not self.is_valid:
            self._name = ['', '']

    @property
    def get_variants(self) -> list[str]:
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


def truncate_chars(text: str, to: int, *, html: bool = False) -> str:
    """Укорачивает поданный на вход текст до опционально указанного количества символов."""
    return Truncator(text).chars(to, html=html)


def truncate_words(text: str, to: int, *, html: bool = False) -> str:
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
    known_items: dict[str, Model | list[Model]],
    unknown_handler: Callable = None
) -> list[str]:
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

                LOG.debug('Handling unknown item in sync_many_to_many(): %s', item)
                val = unknown_handler(item, known_items)

                if val is None:
                    unknown.append(item)
                    continue

            if not isinstance(val, list):
                val = [val]

            for item in val:
                to_add.append(item)  # noqa: PERF402

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
        'QUOTES_REPLACE': (re.compile(r'(„|“|”|(\'\'))'), '"'),
        'DASH_REPLACE': (re.compile(r'(-|­|–|—|―|−|--)'), '-'),

        'SEQUENTIAL_SPACES': (re.compile(r'([ \t]+)'), ' '),

        'DASH_EM': (re.compile(r'([ ,])-[ ]'), '\\g<1>— '),
        'DASH_EN': (re.compile(r'(\d+)[ ]*-[ ]*(\d+)'), '\\g<1>–\\g<2>'),

        'HELLIP': (re.compile(r'\.{2,3}'), '…'),
        'COPYRIGHT': (re.compile(r'\((c|с)\)'), '©'),
        'TRADEMARK': (re.compile(r'\(tm\)'), '™'),
        'TRADEMARK_R': (re.compile(r'\(r\)'), '®'),

        'QUOTES_CYR_CLOSE': (re.compile(r'(\S+)"', re.UNICODE), '\\g<1>»'),
        'QUOTES_CYR_OPEN': (re.compile(r'"(\S+)', re.UNICODE), '«\\g<1>'),
    }

    @classmethod
    def apply_to(cls, input_str: str) -> str:

        input_str = f' {input_str.strip()} '

        for regexp, replacement in cls.rules.values():
            input_str = re.sub(regexp, replacement, input_str)

        return input_str.strip()


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


def search_models(term: str, *, search_in=list[type[models.Model]]) -> tuple[str, list[models.Model]]:
    """Производит поиск указанной строки в указанных областях.
    Возвращает результаты поиска.

    :param term: Строка для посика.
    :param search_in: Области иска.

    """
    search_term = term.strip(' ()')[:200]

    if not search_term:
        return search_term, []

    swapped = swap_layout(search_term)

    results = []

    for model_cls in search_in:
        results.extend(model_cls.find(search_term, swapped))

    return search_term, results
