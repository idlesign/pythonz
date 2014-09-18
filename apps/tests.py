import unittest


from .utils import url_mangle


class UtilsTest(unittest.TestCase):

    def test_url_mangle(self):
        self.assertEqual(url_mangle('http://some.com/path/to/ends?with=this#stuff'), 'http://some.com/<...>ends')
        self.assertEqual(url_mangle('http://some.com/'), 'http://some.com/')
        self.assertEqual(url_mangle('http://some.com'), 'http://some.com')
