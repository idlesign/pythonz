import unittest
from uuid import uuid4


from .generics.models import ModelWithCompiledText
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


class ModelWithCompiledTextTest(unittest.TestCase):

    def test_compile_text(self):
        self.maxDiff = None  # Для наглядности.
        src = '''
**полужирный текст some.where**

*курсив some.where*

http://some.url/

```
здесь цитата
```

Пробуем `ссылку с именем <http://some.com/here/there/>`_.

``текст акцентирован some.where``

.. code:: python

  from come import that


  print(1)
  # комментарий

  print(2)


Далее снова текст.

.. gist:: someuser/gisthashhere

Текст.

'''
        expected = '<b>полужирный текст some.where</b><br><br>' \
                 '<i>курсив some.where</i><br><br>' \
                 '<a href="http://some.url/" target="_blank">http://some.url/</a><br><br>' \
                 '<blockquote>здесь цитата</blockquote><br><br>' \
                 'Пробуем <a href="http://some.com/here/there/" target="_blank">ссылку с именем </a>.<br><br>' \
                 '<code>текст акцентирован some.where</code><br><br>' \
                 '<pre><code class="python"><br>  from come import that<br><br><br>  print(1)<br>  # комментарий<br><br>  print(2)<br></code></pre><br>' \
                 'Далее снова текст.<br><br>' \
                 '<script src="https://gist.github.com/someuser/gisthashhere.js"></script><br>' \
                 'Текст.'

        self.assertEqual(expected.strip('\n'), ModelWithCompiledText.compile_text(src.strip('\n')))


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
