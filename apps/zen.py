from random import choice

from siteblocks.siteblocksapp import register_dynamic_block


ZEN = (
    ('Beautiful is better than ugly.', 'Красивое лучше безобразного.'),
    ('Explicit is better than implicit.', 'Явное лучше подразумеваемого.'),
    ('Simple is better than complex.', 'Простое лучше сложного.'),
    ('Complex is better than complicated.', 'Сложное лучше мудрёного.'),
    ('Flat is better than nested.', 'Плоское лучше вложенного.'),
    ('Sparse is better than dense.', 'Лучше редко, чем кучно.'),
    ('Readability counts.', 'Читабельность всчёт.'),
    ('Special cases aren\'t special enough to break the rules.\nAlthough practicality beats purity.',
     'Исключения недостаточно исключительны, чтобы нарушать правила.\nХотя, практичность превыше чистоты.'),
    ('Errors should never pass silently.\nUnless explicitly silenced.',
     'Ошибки не должны проходить незамеченно.\nЕсли не были заглушены намеренно.'),
    ('In the face of ambiguity, refuse the temptation to guess.',
     'Пред лицом многозначительности презри желание догадаться.'),
    ('There should be one — and preferably only one — obvious way to do it.\n'
     'Although that way may not be obvious at first unless you\'re Dutch.',
     'Должен быть один —  и лучше единственный — очевидный способ достичь цели.\n'
     'Хотя, этот способ поначалу может казаться неочевидным, если вы не голландец.'),
    ('Now is better than never.\nAlthough never is often better than <em>right</em> now.',
     'Лучше теперь, чем никогда.\nХотя, часто никогда, лучше чем <em>сию минуту</em>.'),
    ('If the implementation is hard to explain, it\'s a bad idea.',
     'Если реализацию трудно описать, значит идея была некудышной.'),
    ('If the implementation is easy to explain, it may be a good idea.',
     'Если реализацию легко описать — возможно, идея была хорошей.'),
    ('Namespaces are one honking great idea — let\'s do more of those!',
     'Пространства имён были запредельно замечательной идеей — так понаделаем их ещё!'),
)

register_dynamic_block('zen', lambda **kwargs: choice(ZEN))
