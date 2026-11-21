import re

from django import template
from django.template.defaultfilters import safe
from django.utils.html import conditional_escape

register = template.Library()


RE_HREF = re.compile(r'href="([^"]+)"')


@register.filter
def nolinks(value: str):
    """Убирает из html гиперссылки.

    :param value:

    """
    return safe(f"{RE_HREF.sub('', value)}")


# Разметка особых обозначений справочника. Ранее выполнялась на клиенте (pythonz.js),
# теперь производится на сервере: особые места обрамляются в span с классами,
# оформление задаётся в css и может быть переопределено в js налету.

RE_PYVERSION_ADDED = re.compile(r'\+py([\w.]+)')
RE_PYVERSION_REMOVED = re.compile(r'-py([\w.]+)')
RE_UNDERMETHOD = re.compile(r'(__\S+__)')
RE_EMDASH = re.compile(r'\s+-\s+')
RE_PARAM_ARG = re.compile(r'(?m)^([^->\n]+?)([ \t]--)')
RE_PARAM_HINT = re.compile(r'(\S+)(\s.+)')
RE_PARAM_SEP = re.compile(r'--')
RE_LITERAL_ESCAPED = re.compile(r'&#x27;(.+?)&#x27;')


def _decorate_common(value: str) -> str:
    """Применяет общие правила разметки справочника."""
    value = RE_PYVERSION_REMOVED.sub(
        r'<span class="ref-ver-del" title="Устарело в версии \1">\1</span>', value)
    value = RE_PYVERSION_ADDED.sub(
        r'<span class="ref-ver-add" title="Актуально с версии \1">\1</span>', value)
    return RE_EMDASH.sub(' — ', value)


def _replace_param(match: re.Match) -> str:
    name = match.group(1)
    # Первое слово (имя параметра) выделяем, остальное (умолчания) приглушаем.
    name = RE_PARAM_HINT.sub(r'\1<span class="ref-param-hint">\2</span>', name)
    return f'<span class="ref-param">{name}</span>:'


@register.filter
def ref_marks(value: str):
    """Применяет к html общие правила разметки справочника
    (версии актуальности/устаревания, тире).

    :param value:

    """
    return safe(_decorate_common(value))


@register.filter
def ref_result(value: str):
    """Применяет к описанию результата функции правила разметки справочника.
    Исходный текст экранируется.

    :param value:

    """
    return safe(_decorate_common(conditional_escape(value)))


@register.filter
def ref_params(value: str):
    """Применяет к описанию параметров функции правила разметки справочника.
    Исходный текст экранируется, переводы строк превращаются в <br>.

    :param value:

    """
    value = conditional_escape(value)

    value = RE_PARAM_ARG.sub(_replace_param, value)
    value = RE_PARAM_SEP.sub(':', value)

    value = _decorate_common(value)

    value = RE_LITERAL_ESCAPED.sub(r'<span class="ref-lit">\1</span>', value)
    value = RE_UNDERMETHOD.sub(r'<span class="ref-dunder">\1</span>', value)

    return safe(value.replace('\n', '<br>'))
