from django import forms
from django.forms.widgets import TextInput
from django.forms.utils import flatatt
from django.utils.html import format_html, force_text

from .models import Place


class ReadOnly(forms.Widget):
    """Представляет поле только для чтения."""

    def value_from_datadict(self, data, files, name):
        return getattr(self.model, self.field_name)  # Чтобы поле не считалось изменённым.

    def render(self, name, value, attrs=None):
        if hasattr(self, 'initial'):
            value = self.initial
        return '%s' % (value or '')


class PlaceWidget(TextInput):
    """Представляет поле для редактирования местом."""

    def render(self, name, value, attrs=None):
        if value:
            value = self.model.place.geo_title  # Выводим полное название места.
        return super().render(name, value, attrs=attrs)

    def value_from_datadict(self, data, files, name):
        """Здесь получаем из строки наименования места объект места.

        :param data:
        :param files:
        :param name:
        :return:
        """
        place_name = data.get(name, None)
        if not place_name:
            return ''
        place = Place.create_place_from_name(place_name)
        if place is None:
            return ''
        return place.id


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
                <li><a data-toggle="tab" href="#rst_preview" id="preview_rst" class="xross" data-xevent="click" data-xmethod="POST" data-xtarget="rst_preview" data-xform="edit_form"><span class="glyphicon glyphicon-eye-open"></span> Предпросмотр</a></li>
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
                            Ссылки на внешние ресурсы, начинающиеся с <i>http</i> форматируются автоматически.<br>
                            Можно скрыть ссылку под именем, используя следующий код:<br><br>
                            <pre><code class="nohighlight">Вставка ссылки `под именем&lt;http://pythonz.net/&gt;`_.</code></pre>
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
<pre><code class="nohighlight">```
Это цитата.
```</code></pre>
                        </div>
                    </div>

                    <div class="marg__b_mid">
                        <strong>Исходный код</strong>
                        <div>
                            Подсветка синтаксиса реализуется путём выделения кода в отдельный параграф, начинающийся с инструкции <b>.. code:: имя_языка</b>,
                            где <i>имя_языка</i> &mdash; название языка программирования, например <i>python</i>:<br><br>

<pre><code class="nohighlight">Некий текст.

.. code:: python

    def my_function():
        "just a test"
        print 8/2


И снова текст.</code></pre>
                            * Обратите внимание на необходимость наличия двойного переноса строки после блока кода.
                        </div>
                    </div>


                    <div class="marg__b_mid">
                        <strong>Gist от GitHub</strong>
                        <div>
                            Гисты могут быть вставлены в текст при помощи директивы <b>.. gist:: гитхаб_логин/ид_гиста</b>,
                            где <i>гитхаб_логин</i> &mdash; логин на GitHub, а <i>ид_гиста</i> &mdash; идентификатор гиста.<br>
                            Например, добавим гист с адреса <a href="https://gist.github.com/idlesign/c1255817bb0234d9971a">https://gist.github.com/idlesign/c1255817bb0234d9971a</a>:<br><br>
                            <pre><code class="nohighlight">.. gist:: idlesign/c1255817bb0234d9971a</code></pre>
                            * Обратите внимание на необходимость наличия переноса строки после блока кода.<br>
                            ** Гисты можно создавать по адресу <a href="https://gist.github.com/" target="_blank">https://gist.github.com/</a>
                        </div>
                    </div>


                </div>
            </div>
            ''', flatatt(final_attrs), force_text(value))
