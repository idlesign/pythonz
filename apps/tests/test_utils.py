from ..utils import url_mangle, BasicTypograph


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
