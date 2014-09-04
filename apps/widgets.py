from django import forms
from django.forms.utils import flatatt
from django.utils.html import format_html, force_text


class RstEdit(forms.Widget):
    """Реализует виджет для редактирования и предпросмотра текста в rst-подобном формате."""

    def __init__(self, attrs=None):
        default_attrs = {'cols': '40', 'rows': '10'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None):

        if value is None:
            value = ''

        final_attrs = self.build_attrs(attrs, name=name)

        return format_html('''
            <ul class="nav nav-tabs">
                <li class="active"><a data-toggle="tab" href="#rst_src"><span class="glyphicon glyphicon-edit"></span> Редактирование</a></li>
                <li><a data-toggle="tab" href="#rst_preview" id="preview_rst" class="xross" data-xevent="click" data-xtarget="rst_preview" data-xform="edit_form"><span class="glyphicon glyphicon-eye-open"></span> Предпросмотр</a></li>
                <li><a data-toggle="tab" href="#rst_help"><span class="glyphicon glyphicon-question-sign"></span> Справка по форматированию</a></li>
            </ul>
            <div class="tab-content">
                <div id="rst_src" class="marg__t_min tab-pane fade in active">
                    <textarea{0}>\r\n{1}</textarea>
                </div>
                <div id="rst_preview" class="marg__t_min tab-pane fade"></div>
                <div id="rst_help" class="marg__t_min tab-pane fade">

                    <div class="marg__b_mid">
                        <strong>Строки</strong>
                        <div>
                            Перевод строки трактуется как начало нового параграфа.
                        </div>
                    </div>

                    <div class="marg__b_mid">
                        <strong>Ссылки</strong>
                        <div>
                            Ссылки на внешние ресурсы, начинающиеся с <i>http</i> форматируются автоматически.
                        </div>
                    </div>

                    <div class="marg__b_mid">
                        <strong>Начертание</strong>
                        <div>
                            Для выделения слова или фразы <b>полужирным</b> используйте обрамление в двойные звёзды:<br><br>
                            <pre><code class="nohighlight">Выделение **полужирным**.</code></pre>

                            Для выделения слова или фразы <i>курсивом</i> используйте обрамление в звёзды:<br><br>
                            <pre><code class="nohighlight">Выделение *курсивом*.</code></pre>
                        </div>
                    </div>

                    <div class="marg__b_mid">
                        <strong>Акцентирование</strong>
                        <div>
                            Слово или фразу можно <code>акцентировать</code> путём обрамления в двойные апострофы:<br><br>
                            <pre><code class="nohighlight">Выделение ``акцентом``.</code></pre>
                        </div>
                    </div>

                    <div class="marg__b_mid">
                        <strong>Цитаты</strong>
                        <div>
                            Для оформления цитаты, обрамите её в тройные апострофы:<br><br>
<pre><code class="nohighlight">
```
Это цитата.
```
</code></pre>
                        </div>
                    </div>

                    <div class="marg__b_mid">
                        <strong>Исходный код</strong>
                        <div>
                            Подсветка синтаксиса реализуется путём выделения кода в отдельный параграф, начинающийся с инструкции <b>.. code:: имя_языка</b>,
                            где <i>имя_языка</i> &mdash; название языка программирования, например <i>python</i>:<br><br>

<pre><code class="nohighlight">
Некий текст.

.. code:: python

    def my_function():
        "just a test"
        print 8/2

И снова текст.
</code></pre>
                            * Обратите внимание на наличие перевода строки после блока кода.
                        </div>
                    </div>


                </div>
            </div>
            ''', flatatt(final_attrs), force_text(value))
