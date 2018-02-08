from pythonz.apps.utils import url_mangle, BasicTypograph, TextCompiler, PersonName, swap_layout


def test_person_name():
    name = PersonName('Иван Иванов')

    assert name.first_last == 'Иван Иванов'
    assert name.last_first == 'Иванов Иван'
    assert name.full == 'Иван Иванов'
    assert name.short == 'И. Иванов'
    assert name.first == 'Иван'
    assert name.last == 'Иванов'
    assert name.is_valid
    assert len(name.get_variants()) == 3

    name = PersonName('Guido van Rossum')

    assert name.first_last == 'Guido Rossum'
    assert name.last_first == 'Rossum Guido'
    assert name.full == 'Guido van Rossum'
    assert name.short == 'G. van Rossum'
    assert name.first == 'Guido'
    assert name.last == 'Rossum'
    assert name.is_valid
    assert len(name.get_variants()) == 4

    name = PersonName('Натаниэль Дж. Смит')

    assert name.first_last == 'Натаниэль Смит'
    assert name.last_first == 'Смит Натаниэль'
    assert name.full == 'Натаниэль Дж. Смит'
    assert name.short == 'Н. Дж. Смит'
    assert name.first == 'Натаниэль'
    assert name.last == 'Смит'
    assert name.is_valid
    assert len(name.get_variants()) == 4

    name = PersonName('Петров')

    assert name.first_last == ''
    assert name.last_first == ''
    assert name.full == ''
    assert name.short == ''
    assert name.first == ''
    assert name.last == ''
    assert not name.is_valid
    assert name.get_variants() == []


def test_url_mangle():

    assert url_mangle('http://some.com/not/very/long/url') == 'http://some.com/not/very/long/url'
    assert url_mangle('http://some.com/path/to/some/resource/which/ends?with=this#stuff') == 'http://some.com/<...>ends'
    assert url_mangle('http://some.com/') == 'http://some.com/'
    assert url_mangle('http://some.com'), 'http://some.com'


def test_typography():
    input_str = "Мама     ''мыла'' раму. " \
                'Фабрика “Красная Заря”. ' \
                '"Маме - раму!",- кричал\tИван. ' \
                'Температура повысилась на 7-8 градусов. ' \
                '(c), (r), (tm) заменяем на правильные. ' \
                '"строка\nперенесена'

    expected_str = 'Мама «мыла» раму. ' \
                   'Фабрика «Красная Заря». ' \
                   '«Маме — раму!»,— кричал Иван. ' \
                   'Температура повысилась на 7–8 градусов. ' \
                   '©, ®, ™ заменяем на правильные. ' \
                   '«строка\nперенесена'

    assert BasicTypograph.apply_to(input_str) == expected_str


def test_text_compiler():

    compile = TextCompiler.compile

    assert (
        'is <a href="https://some.org">https://some.org</a></td>' in
        compile('.. table::\n`one / two<https://some.com>`_ - is https://some.org\nanother\n\n\n')
    )

    assert compile('2 ** 10d') == '2 ** 10d'

    assert (
        compile('``zip(*[iter(s)] * n)``\nlist(zip(*[iter(seq)] * 2))  # [(1, 2), (3, 4), (5, 6)]') ==
        '<code>zip(*[iter(s)] * n)</code><br>list(zip(*[iter(seq)] * 2))  # [(1, 2), (3, 4), (5, 6)]')

    assert compile('2 ** 10d') == '2 ** 10d'

    assert compile('**some**') == '<b>some</b>'
    assert compile('*some*') == '<i>some</i>'
    assert compile('```\nздесь цитата\n```') == '<blockquote>здесь цитата</blockquote>'

    assert compile('``some``') == '<code>some</code>'

    assert compile('http://some.url/') == '<a href="http://some.url/">http://some.url/</a>'
    assert compile(
        '`This is httpserver link<http://some.url/>`_') == '<a href="http://some.url/">This is httpserver link</a>'
    assert (
        compile('Пробуем `ссылку с [именем] <http://some.com/here/there/>`_.') ==
        'Пробуем <a href="http://some.com/here/there/">ссылку с [именем] </a>.')

    assert compile('\n* Some.\n\n') == '<br><ul><li>Some.</li></ul><br>'
    assert compile('\n* Some.\n* Other.\n\n') == '<br><ul><li>Some.</li><li>Other.</li></ul><br>'

    assert (
        compile('.. gist:: someuser/gisthashhere\n') ==
        '<script src="https://gist.github.com/someuser/gisthashhere.js"></script>')

    assert (
        compile('.. podster:: http://mtpod.podster.fm/0\n') ==
        '<iframe width="100%" height="85" src="http://mtpod.podster.fm/0/embed/13?link=1" '
        'frameborder="0" allowtransparency="true"></iframe>')

    assert (
        compile('.. image:: http://some.url/img.png\n') ==
        '<img alt="http://some.url/img.png" src="http://some.url/img.png" '
        'data-canonical-src="http://some.url/img.png" style="max-width:100%;">')

    assert (
        compile('.. code:: python\nprint("some")\n\n\n') ==
        '<pre><code class="python">print("some")</code></pre><br>')

    assert (
        compile('.. code:: html\nprint("some")\n\n\n') ==
        '<pre><code class="html">print("some")</code></pre><br>')

    assert (
        compile('.. table::\n``x(?<!y)`` | 2|2 | 3 \n4 | 5 | 6\n\n\n') ==
        '<div class="table-responsive"><table class="table table-striped table-bordered table-hover">'
        '<tr><td><code>x(?&lt;!y)</code></td><td>2|2</td><td>3</td></tr><tr><td>4</td><td>5</td><td>6</td></tr></table></div><br>')

    assert (
        compile('.. table::\n! 1 | 2 | 3\n4 | 5 | 6\n\n\n') ==
        '<div class="table-responsive"><table class="table table-striped table-bordered table-hover">'
        '<thead><tr><th>1</th><th>2</th><th>3</th></tr></thead><tr><td>4</td><td>5</td><td>6</td></tr></table></div><br>')

    assert (
        compile('.. table::\n!b:d+ 1 | 2 | 3 \n 4 | !b:i 5 | 6\n\n\n') ==
        '<div class="table-responsive"><table class="table table-striped table-bordered table-hover">'
        '<tr class="danger"><td>1</td><td>2</td><td>3</td></tr>'
        '<tr><td>4</td><td class="info">5</td><td>6</td></tr></table></div><br>')

    assert (
        compile('.. note:: a note\n') ==
        '<div class="panel panel-primary"><div class="panel-heading">На заметку</div><div class="panel-body">a note</div></div>')

    assert (
        compile('.. warning:: a warn\n') ==
        '<div class="panel panel-danger"><div class="panel-heading">Внимание</div><div class="panel-body">a warn</div></div>')


def test_swap_layout():
    assert swap_layout('вуа') == 'def'
    assert not swap_layout('def')
    assert swap_layout('Ш рфму ыуут ьщку ерфт ьщыею') == 'I have seen more than most.'
