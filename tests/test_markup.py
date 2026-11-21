from pythonz.apps.markup import compile_markdown


def test_inline_formatting():

    assert compile_markdown('**some**') == '<p><strong>some</strong></p>\n'
    assert compile_markdown('*some*') == '<p><em>some</em></p>\n'
    assert compile_markdown('``some``') == '<p><code>some</code></p>\n'

    assert '2 ** 10d' in compile_markdown('2 ** 10d')


def test_links():

    assert (
        compile_markdown('http://some.url/') ==
        '<p><a href="http://some.url/">http://some.url/</a></p>\n')

    assert (
        compile_markdown('[This is httpserver link](http://some.url/)') ==
        '<p><a href="http://some.url/">This is httpserver link</a></p>\n')

    # Длинные URL в автоссылках укорачиваются для отображения.
    assert (
        compile_markdown('http://some.com/path/to/some/resource/which/ends?with=this#stuff') ==
        '<p><a href="http://some.com/path/to/some/resource/which/ends?with=this#stuff">'
        'http://some.com/&lt;...&gt;ends</a></p>\n')


def test_lists():

    assert (
        compile_markdown('* Some.\n* Other.\n') ==
        '<ul>\n<li>Some.</li>\n<li>Other.</li>\n</ul>\n')


def test_quotes():

    assert compile_markdown('> здесь цитата') == '<blockquote>\n<p>здесь цитата</p>\n</blockquote>\n'


def test_code_fence():

    assert (
        compile_markdown('```python\nprint("some")\n```') ==
        '<pre><code class="python">print(&quot;some&quot;)\n</code></pre>\n')

    assert (
        compile_markdown('```\nprint("some")\n```') ==
        '<pre><code class="python">print(&quot;some&quot;)\n</code></pre>\n')

    assert (
        compile_markdown('```bash\nls -la\n```') ==
        '<pre><code class="bash">ls -la\n</code></pre>\n')


def test_embeds():

    assert (
        compile_markdown('```gist\nsomeuser/gisthashhere\n```') ==
        '<script src="https://gist.github.com/someuser/gisthashhere.js"></script>')

    assert (
        compile_markdown('```podcast\nhttp://mtpod.podster.fm/0\n```') ==
        '<iframe width="100%" height="85" src="http://mtpod.podster.fm/0/embed/13?link=1" '
        'frameborder="0" allowtransparency="true"></iframe>')

    compiled = compile_markdown('```poll\nabsdefgh\n```')
    assert 'absdefgh' in compiled
    assert 'yastatic' in compiled

    assert (
        compile_markdown('```video\nhttps://youtu.be/ZE7WsnmGZ3U?t=10\n```') ==
        '<div class="embed-responsive embed-responsive-16by9">'
        '<iframe src="//www.youtube.com/embed/ZE7WsnmGZ3U?start=10&rel=0" '
        'width="560" height="315" frameborder="0" allowfullscreen></iframe></div>')


def test_image():

    assert (
        compile_markdown('![alt](http://some.url/img.png)') ==
        '<p><img alt="alt" src="http://some.url/img.png" '
        'data-canonical-src="http://some.url/img.png" style="max-width:100%;"></p>\n')


def test_table():

    compiled = compile_markdown('| 1 | 2 |\n|---|---|\n| 3 | 4 |')

    assert compiled.startswith(
        '<div class="table-responsive"><table class="table table-striped table-bordered table-hover">')
    assert compiled.endswith('</table></div>\n')
    assert '<th>1</th>' in compiled
    assert '<td>3</td>' in compiled


def test_admonitions():

    assert (
        compile_markdown('!!! note\n    a note\n') ==
        '<div class="card mb-3"><div class="card-header text-white bg-success">'
        'На заметку</div><div class="card-body"><p>a note</p>\n</div></div>')

    assert (
        compile_markdown('!!! warning\n    a warn\n') ==
        '<div class="card mb-3"><div class="card-header text-white bg-danger">'
        'Внимание</div><div class="card-body"><p>a warn</p>\n</div></div>')

    # Явно заданный заголовок имеет приоритет над умолчательным.
    assert (
        compile_markdown('!!! warning "Свой заголовок"\n    a warn\n') ==
        '<div class="card mb-3"><div class="card-header text-white bg-danger">'
        'Свой заголовок</div><div class="card-body"><p>a warn</p>\n</div></div>')


def test_subtitle():

    assert (
        compile_markdown('#### Подзаголовок') ==
        '<h4 data-geopattern="Подзаголовок" class="subtitle">Подзаголовок</h4>\n')


def test_breaks():

    assert compile_markdown('строка1\nстрока2') == '<p>строка1<br />\nстрока2</p>\n'
    assert compile_markdown('строка1\nстрока2', breaks=False) == '<p>строка1\nстрока2</p>\n'


def test_raw_html_escaped():

    assert (
        compile_markdown('текст <script>alert(1)</script>') ==
        '<p>текст &lt;script&gt;alert(1)&lt;/script&gt;</p>\n')


def test_self_links_normalized():
    """Ссылки на собственный домен становятся относительными."""

    assert (
        compile_markdown('[x](http://pythonz.net/articles/47/)') ==
        '<p><a href="/articles/47/">x</a></p>\n')

    assert (
        compile_markdown('[x](https://www.pythonz.net/references/)') ==
        '<p><a href="/references/">x</a></p>\n')

    # Автоссылки тоже нормализуются (отображаемый текст сохраняется).
    assert (
        compile_markdown('http://pythonz.net/x/') ==
        '<p><a href="/x/">http://pythonz.net/x/</a></p>\n')

    # Внешние ссылки не трогаются.
    assert (
        compile_markdown('[x](https://example.com/a)') ==
        '<p><a href="https://example.com/a">x</a></p>\n')


def test_fuzzy_linkify_off():
    """Автоссылки создаются только из URL с явной схемой."""

    assert (
        compile_markdown('файл MANIFEST.in и pythonz.net и http://x.ru/a') ==
        '<p>файл MANIFEST.in и pythonz.net и <a href="http://x.ru/a">http://x.ru/a</a></p>\n')


def test_footnotes():

    compiled = compile_markdown('Текст.[^1]\n\n[^1]: Сноска.')
    assert '<sup class="footnote-ref">' in compiled
    assert 'Текст сноски' not in compiled or 'Сноска.' in compiled
