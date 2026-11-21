"""Инструменты для работы с markdown-разметкой текстов (см. #95).

"""
import re

from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml
from markdown_it.renderer import RendererHTML
from mdit_py_plugins.admon import admon_plugin
from mdit_py_plugins.footnote import footnote_plugin

from .exceptions import RemoteSourceError
from .integration.videos import VideoBroker
from .utils import url_mangle

#: URL собственного домена (нормализуются в относительные).
RE_SELF_URL = re.compile(r'^https?://(?:www\.)?pythonz\.net(/?)', re.IGNORECASE)

#: Заголовки и фоновые классы для примечаний (admonitions).
ADMON_KINDS: dict[str, tuple[str, str]] = {
    'note': ('На заметку', 'bg-success'),
    'warning': ('Внимание', 'bg-danger'),
}


def _render_embed_video(url: str) -> str:
    try:
        code, _ = VideoBroker.get_code_and_cover(url, wrap_responsive=True)

    except RemoteSourceError:
        code = '<b>Ошибка встраивания видео: неподдерживаемый сервис.</b>'

    return code


def _render_embed_gist(gist: str) -> str:
    return f'<script src="https://gist.github.com/{escapeHtml(gist)}.js"></script>'


def _render_embed_podcast(url: str) -> str:
    """Отрисовывает проигрыватель подкаста с podster.fm."""
    url = escapeHtml(url)
    return (
        f'<iframe width="100%" height="85" src="{url}/embed/13?link=1" '
        'frameborder="0" allowtransparency="true"></iframe>')


def _render_embed_poll(poll_id: str) -> str:
    poll_id = escapeHtml(poll_id)
    return (
        '<div class="card bg-light p-2 m-2"><div class="card-body">'
        '<script src="https://yastatic.net/q/forms-frontend-ext/_/embed.js"></script>'
        f'<iframe src="https://forms.yandex.ru/u/{poll_id}/?iframe=1" '
        f'frameborder="0" width="100%" name="ya-form-{poll_id}"></iframe></div></div>')


EMBED_RENDERERS = {
    'video': _render_embed_video,
    'gist': _render_embed_gist,
    'podcast': _render_embed_podcast,
    'poll': _render_embed_poll,
}


class RendererPythonz(RendererHTML):
    """Рендерер markdown в HTML с учётом особенностей pythonz."""

    def fence(self, tokens, idx, options, env) -> str:
        """Отрисовывает ограждённые блоки кода и вставки (видео, гисты и пр.)."""
        token = tokens[idx]
        info = token.info.strip()
        lang = info.split(None, 1)[0] if info else ''

        if lang in EMBED_RENDERERS:
            return EMBED_RENDERERS[lang](token.content.strip())

        return f'<pre><code class="{lang or "python"}">{escapeHtml(token.content)}</code></pre>\n'

    def table_open(self, tokens, idx, options, env) -> str:
        return (
            '<div class="table-responsive">'
            '<table class="table table-striped table-bordered table-hover">')

    def table_close(self, tokens, idx, options, env) -> str:
        return '</table></div>\n'

    def heading_open(self, tokens, idx, options, env) -> str:
        token = tokens[idx]

        if token.tag == 'h4':
            # Подзаголовки с геоузором.
            title = escapeHtml(tokens[idx + 1].content)
            return f'<h4 data-geopattern="{title}" class="subtitle">'

        return self.renderToken(tokens, idx, options, env)

    def image(self, tokens, idx, options, env) -> str:
        token = tokens[idx]
        src = escapeHtml(token.attrGet('src') or '')
        alt = escapeHtml(token.content)
        return f'<img alt="{alt}" src="{src}" data-canonical-src="{src}" style="max-width:100%;">'


def _render_admonition(self, tokens, idx, options, env) -> str:
    """Отрисовывает примечания (admonitions) вида "!!! note" в карточки Bootstrap."""
    token = tokens[idx]

    if token.type == 'admonition_open':
        title_default, bg = ADMON_KINDS.get(token.meta['tag'], (token.meta['tag'].capitalize(), 'bg-info'))
        title = token.meta.get('title') or title_default
        return (
            f'<div class="card mb-3"><div class="card-header text-white {bg}">{title}</div>'
            '<div class="card-body">')

    if token.type == 'admonition_close':
        return '</div></div>'

    # Токены заголовка (admonition_title_*) удаляются правилом _fold_admon_titles,
    # здесь они не должны оказаться.
    return ''


def _fold_admon_titles(state) -> None:
    """Переносит заголовок примечания в meta открывающего токена и удаляет токены заголовка."""
    tokens = state.tokens
    result = []
    skip = 0

    for idx, token in enumerate(tokens):
        if skip:
            skip -= 1
            continue

        if token.type == 'admonition_title_open' and result:
            # Далее идут inline с заголовком и admonition_title_close.
            title = tokens[idx + 1].content
            opening = result[-1]
            kind = opening.meta['tag']
            if title != kind.capitalize():
                # Заголовок задан автором явно, используем его.
                opening.meta['title'] = title
            skip = 2
            continue

        result.append(token)

    state.tokens = result


def _mangle_autolinks(state) -> None:
    """Укорачивает для отображения текст автоматически созданных из URL ссылок."""
    for token in state.tokens:
        if token.type != 'inline':
            continue

        children = token.children or []

        for idx, child in enumerate(children[:-1]):
            if child.type != 'link_open':
                continue

            href = child.attrGet('href') or ''
            text_token = children[idx + 1]

            if text_token.type == 'text' and text_token.content == href and href.startswith('http'):
                text_token.content = url_mangle(href)


def _normalize_self_links(self, tokens, idx, options, env) -> str:
    """Нормализует ссылки на собственный домен в относительные."""
    token = tokens[idx]
    href = token.attrGet('href') or ''

    if href:
        token.attrSet('href', RE_SELF_URL.sub(r'\g<1>', href))

    return self.renderToken(tokens, idx, options, env)


_MD_ENGINES: dict[bool, MarkdownIt] = {}


def get_engine(*, breaks: bool = True) -> MarkdownIt:
    """Возвращает кешированный экземпляр markdown-движка.

    :param breaks: Переводить ли одиночные переводы строк в <br>.

    """
    engine = _MD_ENGINES.get(breaks)

    if engine is None:
        engine = MarkdownIt(
            'commonmark',
            {'breaks': breaks, 'linkify': True, 'html': False},
            renderer_cls=RendererPythonz,
        ).enable(['table', 'linkify'])

        # Сохраняем прежнее поведение: автоссылками становятся только
        # URL с явной схемой http(s), но не домены и адреса почты.
        engine.linkify.set({'fuzzy_link': False, 'fuzzy_email': False, 'fuzzy_ip': False})

        admon_plugin(engine, render=_render_admonition)
        footnote_plugin(engine)
        engine.add_render_rule('link_open', _normalize_self_links)
        engine.core.ruler.push('fold_admon_titles', _fold_admon_titles)
        engine.core.ruler.push('mangle_autolinks', _mangle_autolinks)

        _MD_ENGINES[breaks] = engine

    return engine


def compile_markdown(text: str, *, breaks: bool = True) -> str:
    """Преобразует markdown-форматирование в html.

    :param text:
    :param breaks: Переводить ли одиночные переводы строк в <br>.

    """
    text = text.replace('\r\n', '\n')
    return get_engine(breaks=breaks).render(text)
