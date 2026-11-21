from pythonz.apps.templatetags.text import ref_marks, ref_params, ref_result


def test_ref_marks():

    assert (
        ref_marks('Актуально с +py3.9 и далее') ==
        'Актуально с <span class="ref-ver-add" title="Актуально с версии 3.9">3.9</span> и далее')

    assert (
        ref_marks('Устарело с -py2.7 и далее') ==
        'Устарело с <span class="ref-ver-del" title="Устарело в версии 2.7">2.7</span> и далее')

    assert ref_marks('раз - два') == 'раз — два'


def test_ref_result():

    assert ref_result('<b>int</b>') == '&lt;b&gt;int&lt;/b&gt;'
    assert ref_result('int +py3.8') == 'int <span class="ref-ver-add" title="Актуально с версии 3.8">3.8</span>'


def test_ref_params():

    assert (
        ref_params('args -- Аргументы.') ==
        '<span class="ref-param">args</span>: Аргументы.')

    assert (
        ref_params('kwargs=None -- Аргументы.') ==
        '<span class="ref-param">kwargs=None</span>: Аргументы.')

    assert (
        ref_params('args, kwargs=None -- Аргументы.') ==
        '<span class="ref-param">args,<span class="ref-param-hint"> kwargs=None</span></span>: Аргументы.')

    compiled = ref_params("arg -- Указать 'all' для __init__\nвторой -- ряд")
    assert '<span class="ref-lit">all</span>' in compiled
    assert '<span class="ref-dunder">__init__</span>' in compiled
    assert '<br>' in compiled

    # Текст экранируется.
    assert ref_params('<script> -- x') == '<span class="ref-param">&lt;script&gt;</span>: x'


def test_ref_params_multiline():
    """Имя параметра не перескакивает через перевод строки."""

    compiled = ref_params('Один аргумент:\nobj -- Объект.')
    assert compiled == 'Один аргумент:<br><span class="ref-param">obj</span>: Объект.'
