import unittest
from uuid import uuid4


from .utils import url_mangle
from .models import User, Opinion


def create_user():
    user = User(username='user%s' % uuid4().hex)
    user.save()
    return user


class UtilsTest(unittest.TestCase):

    def test_url_mangle(self):
        self.assertEqual(url_mangle('http://some.com/not/very/long/url'), 'http://some.com/not/very/long/url')
        self.assertEqual(url_mangle('http://some.com/path/to/some/resource/which/ends?with=this#stuff'), 'http://some.com/<...>ends')
        self.assertEqual(url_mangle('http://some.com/'), 'http://some.com/')
        self.assertEqual(url_mangle('http://some.com'), 'http://some.com')


class ModelOpinionTest(unittest.TestCase):

    def test_new(self):
        user = create_user()
        o = Opinion(submitter=user, linked_object=user, text_src='проба пера')
        o.save()

        self.assertIsNone(o.time_modified)
        self.assertIsNotNone(o.time_published)
        self.assertIsNotNone(o.time_created)
        self.assertEqual(o.status, o.STATUS_PUBLISHED)
        self.assertEqual(o.text_src, 'проба пера')
        self.assertEqual(o.title, '%s про «%s»' % (user.get_display_name(), o.linked_object.title))
