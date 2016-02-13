from random import choice

from siteblocks.siteblocksapp import register_dynamic_block


ZEN = (
    ('Beautiful is better than ugly.', 'Красивое лучше безобразного.'),
    ('Explicit is better than implicit.', 'Явное лучше подразумеваемого.'),
    ('Simple is better than complex.', 'Простое лучше сложного.'),
    ('Complex is better than complicated.', 'Сложное лучше усложнённого.'),
    ('Flat is better than nested.', 'Плоское лучше вложенного.'),
    ('Sparse is better than dense.', 'Разреженное лучше плотного.'),
    ('Readability counts.', 'Важна читабельность.'),
    ('Special cases aren\'t special enough to break the rules.\nAlthough practicality beats purity.',
     'Исключения недостаточно исключительны, чтобы нарушать правила.\nХотя, практичность превыше безупречности.'),
    ('Errors should never pass silently.\nUnless explicitly silenced.',
     'Ошибки не должны оставаться незамеченными.\nЕсли не были заглушены явно.'),
    ('In the face of ambiguity, refuse the temptation to guess.',
     'Пред лицом многозначности презрите желание догадываться.'),
    ('There should be one — and preferably only one — obvious way to do it.\n'
     'Although that way may not be obvious at first unless you\'re Dutch.',
     'Должен быть один — и лучше единственный — очевидный способ достичь цели.\n'
     'Впрочем, если вы не голландец, поначалу этот способ может казаться не столь очевидным.'),
    ('Now is better than never.\nAlthough never is often better than <em>right</em> now.',
     'Лучше сейчас, чем никогда.\nВпрочем, часто <em>никогда</em> лучше, чем <em>прямо сейчас</em>.'),
    ('If the implementation is hard to explain, it\'s a bad idea.',
     'Если реализацию трудно описать, значит идея была никудышной.'),
    ('If the implementation is easy to explain, it may be a good idea.',
     'Если реализацию легко описать — возможно, идея была хорошей.'),
    ('Namespaces are one honking great idea — let\'s do more of those!',
     'Пространства имён были блестящей идеей — генерируем ещё!'),
)


def register_zen_siteblock():
    """Регистрирует динамический блок сайта, наполняемый цитатами из дзена."""
    register_dynamic_block('zen', lambda **kwargs: choice(ZEN))
