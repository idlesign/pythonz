from pythonz.apps.utils import BasicTypograph, PersonName, swap_layout, url_mangle


def test_person_name():

    name = PersonName('Иван Иванов')

    assert name.first_last == 'Иван Иванов'
    assert name.last_first == 'Иванов Иван'
    assert name.full == 'Иван Иванов'
    assert name.short == 'И. Иванов'
    assert name.first == 'Иван'
    assert name.last == 'Иванов'
    assert name.is_valid
    assert len(name.get_variants) == 3

    name = PersonName('Guido van Rossum')

    assert name.first_last == 'Guido Rossum'
    assert name.last_first == 'Rossum Guido'
    assert name.full == 'Guido van Rossum'
    assert name.short == 'G. van Rossum'
    assert name.first == 'Guido'
    assert name.last == 'Rossum'
    assert name.is_valid
    assert len(name.get_variants) == 4

    name = PersonName('Натаниэль Дж. Смит')

    assert name.first_last == 'Натаниэль Смит'
    assert name.last_first == 'Смит Натаниэль'
    assert name.full == 'Натаниэль Дж. Смит'
    assert name.short == 'Н. Дж. Смит'
    assert name.first == 'Натаниэль'
    assert name.last == 'Смит'
    assert name.is_valid
    assert len(name.get_variants) == 4

    name = PersonName('Петров')

    assert name.first_last == ''
    assert name.last_first == ''
    assert name.full == ''
    assert name.short == ''
    assert name.first == ''
    assert name.last == ''
    assert not name.is_valid
    assert name.get_variants == []


def test_url_mangle():

    assert url_mangle('http://some.com/not/very/long/url') == 'http://some.com/not/very/long/url'
    assert url_mangle('http://some.com/path/to/some/resource/which/ends?with=this#stuff') == 'http://some.com/<...>ends'
    assert url_mangle('http://some.com/') == 'http://some.com/'
    assert url_mangle('http://some.com'), 'http://some.com'


def test_typography():

    input_str = ("Мама     ''мыла'' раму. "
                'Фабрика “Красная Заря”. '
                '"Маме - раму!",- кричал\tИван. '
                'Температура повысилась на 7-8 градусов. '
                '(c), (r), (tm) заменяем на правильные. '
                '"строка\nперенесена')

    expected_str = ('Мама «мыла» раму. '
                   'Фабрика «Красная Заря». '
                   '«Маме — раму!»,— кричал Иван. '
                   'Температура повысилась на 7–8 градусов. '
                   '©, ®, ™ заменяем на правильные. '
                   '«строка\nперенесена')

    assert BasicTypograph.apply_to(input_str) == expected_str


def test_swap_layout():
    assert swap_layout('вуа') == 'def'
    assert not swap_layout('def')
    assert swap_layout('Ш рфму ыуут ьщку ерфт ьщыею') == 'I have seen more than most.'
