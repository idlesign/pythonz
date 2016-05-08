from ...generics.models import ModelWithCompiledText


def test_compile_text():

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

.. podster:: http://mtpod.podster.fm/0

Далее.

'''
    expected = (
        '<b>полужирный текст some.where</b><br><br>'
        '<i>курсив some.where</i><br><br>'
        '<a href="http://some.url/">http://some.url/</a><br><br>'
        '<blockquote>здесь цитата</blockquote><br><br>'
        'Пробуем <a href="http://some.com/here/there/">ссылку с именем </a>.<br><br>'
        '<code>текст акцентирован some.where</code><br><br>'
        '<pre><code class="python"><br>  from come import that<br><br><br>  print(1)<br>'
        '  # комментарий<br><br>  print(2)<br></code></pre><br>'
        'Далее снова текст.<br><br>'
        '<script src="https://gist.github.com/someuser/gisthashhere.js"></script><br>'
        'Текст.<br><br>'
        '<iframe width="100%" height="85" '
        'src="http://mtpod.podster.fm/0/embed/13?link=1" frameborder="0" allowtransparency="true"></iframe>'
        '<br>'
        'Далее.'
    )

    assert ModelWithCompiledText.compile_text(src.strip('\n')) == expected.strip('\n')
