from ..utils import url_mangle, BasicTypograph, TextCompiler


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

    assert compile('**some**') == '<b>some</b>'
    assert compile('*some*') == '<i>some</i>'
    assert compile('```\nздесь цитата\n```') == '<blockquote>здесь цитата</blockquote>'

    assert compile('``some``') == '<code>some</code>'

    assert compile('http://some.url/') == '<a href="http://some.url/">http://some.url/</a>'
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
        compile('.. table::\n1|2|3\n4|5|6\n\n\n') ==
        '<div class="table-responsive"><table class="table table-striped table-bordered table-hover">'
        '<tr><td>1</td><td>2</td><td>3</td></tr><tr><td>4</td><td>5</td><td>6</td></tr></table></div><br>')

    assert (
        compile('.. table::\n! 1|2|3\n4|5|6\n\n\n') ==
        '<div class="table-responsive"><table class="table table-striped table-bordered table-hover">'
        '<thead><tr><th>1</th><th>2</th><th>3</th></tr></thead><tr><td>4</td><td>5</td><td>6</td></tr></table></div><br>')

    assert (
        compile('.. note:: a note\n') ==
        '<div class="panel panel-primary"><div class="panel-heading">На заметку</div><div class="panel-body">a note</div></div>')

    assert (
        compile('.. warning:: a warn\n') ==
        '<div class="panel panel-danger"><div class="panel-heading">Внимание</div><div class="panel-body">a warn</div></div>')


