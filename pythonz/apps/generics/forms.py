from datetime import datetime

from django import forms
from django.forms.widgets import CheckboxInput

from ..models import Article
from ..forms.widgets import RstEditWidget


class CommonEntityForm(forms.ModelForm):
    """Базовый класс для форм создания/редактирования сущностей."""

    def clean_year(self):
        year = self.cleaned_data['year'] or ''
        year = year.strip()
        if year:
            if len(year) != 4 or not year.isdigit() or not (1900 < int(year) <= datetime.now().year):
                raise forms.ValidationError('Такой год не похож на правду.')
        return year


class RealmEditBaseForm(CommonEntityForm):
    """Базовый класс для форм создания/редактирования сущностей, принадлежащим областям."""

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if self._meta.model is not Article:  # Запрещаем управлять статусом везде, кроме Статей.
            if user is not None:
                if not user.is_superuser and not user.is_staff:
                    try:
                        del self.fields['status']
                    except KeyError:  # Нет такого поля на форме.
                        pass

        instance = kwargs.get('instance', None)
        for field_name in self.fields:
            fld = self.fields[field_name]

            if field_name == 'description':
                fld.widget = forms.Textarea(attrs={'rows': 3})

            elif field_name == 'text_src':
                fld.widget = RstEditWidget(attrs={'rows': 12})
                fld.strip = False  # Обрубать размеченный текст не следует.

            # Эти изменения нужны для стилизации форм.
            if isinstance(self.fields[field_name].widget, CheckboxInput):
                self.fields[field_name].is_checkbox = True
            fld.widget.attrs['class'] = 'form-control input-sm'

            # Эти связи потребуются в некоторых виджетах.
            fld.widget.model = instance
            fld.widget.field_name = field_name
