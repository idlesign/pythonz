from types import SimpleNamespace

from pythonz.apps.views.references import shorten_tree_titles


def make_items(*titles):
    return [SimpleNamespace(title=title) for title in titles]


def test_shorten_tree_titles_common_prefix():

    items = make_items('object.__add__', 'object.__init__', 'object.__str__', 'list')

    shorten_tree_titles(items)

    assert [item.title_short for item in items] == ['__add__', '__init__', '__str__', 'list']


def test_shorten_tree_titles_prefix_threshold():

    items = make_items('os.walk', 'os.path')

    shorten_tree_titles(items)

    assert [item.title_short for item in items] == ['os.walk', 'os.path']


def test_shorten_tree_titles_longest_prefix():

    items = make_items('os.path.join', 'os.path.split', 'os.path.exists', 'os.walk')

    shorten_tree_titles(items)

    assert [item.title_short for item in items] == ['join', 'split', 'exists', 'walk']


def test_shorten_tree_titles_no_prefixes():

    items = make_items('abs', 'all', 'any')

    shorten_tree_titles(items)

    assert [item.title_short for item in items] == ['abs', 'all', 'any']


def test_shorten_tree_titles_trailing_dot():

    items = make_items('object.', 'object.__add__', 'object.__init__', 'object.__str__')

    shorten_tree_titles(items)

    assert [item.title_short for item in items] == ['object.', '__add__', '__init__', '__str__']
