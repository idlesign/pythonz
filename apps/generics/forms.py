from datetime import datetime

from django import forms


class CommonEntityForm(forms.ModelForm):
    """Базовый класс для форм создания/редактирования сущностей."""

    def clean_year(self):
        year = self.cleaned_data['year'].strip()
        if year:
            if len(year) != 4 or not year.isdigit() or not (1900 < int(year) <= datetime.now().year):
                raise forms.ValidationError('Такой год не похож на правду.')
        return year


class RealmEditBaseForm(CommonEntityForm):
    """Базовый класс для форм создания/редактирования сущностей, принадлежащим областям."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
