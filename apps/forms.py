from django import forms

from .models import Book, Video, Event, Opinion, User, Article
from .widgets import RstEdit
from .generics.forms import RealmEditBaseForm
from .utils import PROJECT_SOURCE_URL


class OpinionForm(RealmEditBaseForm):

    class Meta:
        model = Opinion
        fields = ('text_src',)
        labels = {'text_src': ''}
        widgets = {'text_src': RstEdit(attrs={'rows': 15})}


class ArticleForm(RealmEditBaseForm):
    
    class Meta:
        model = Article
        fields = (
            'title',
            'description',
            'status',
            'text_src'
        )
        labels = {
            'description': 'Введение',
            'text_src': ''
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'text_src': RstEdit(attrs={'rows': 25}),
        }


class BookForm(RealmEditBaseForm):

    class Meta:
        model = Book
        fields = (
            'title',
            'description',
            'status',
            'author',
            'translator',
            'year',
            'cover',
            'isbn',
            'isbn_ebook'
        )

    @staticmethod
    def clean_isbn_(isbn):
        isbn = isbn.replace('-', '').strip()
        length = len(isbn)
        if length:
            if (length != 10 and length != 13) or not isbn.isdigit():
                raise forms.ValidationError('Код ISBN должен содержать 10, либо 13 цифр.')
        return isbn

    def clean_isbn(self):
        return self.clean_isbn_(self.cleaned_data['isbn'])

    def clean_isbn_ebook(self):
        return self.clean_isbn_(self.cleaned_data['isbn_ebook'])


class VideoForm(RealmEditBaseForm):

    class Meta:
        model = Video
        fields = (
            'title',
            'url',
            'description',
            'status',
            'author',
            'translator',
            'year',
        )
        help_texts = {
            'url': 'URL страницы с видео. Умеем работать с %s' % ', '.join(Video.get_supported_hostings()),
        }

    def clean_url(self):
        url = self.cleaned_data['url']
        if not Video.get_hosting_for_url(url):
            raise forms.ValidationError('К сожалению, мы не умеем работать с этим видео-хостингом. Если знаете, как это исправить, приходите <a href="%s">сюда</a>.' % PROJECT_SOURCE_URL)
        return url

    def save(self, *args, **kwargs):
        self.instance.update_code_and_cover(self.cleaned_data['url'])
        return super().save(*args, **kwargs)


class EventForm(RealmEditBaseForm):

    class Meta:
        model = Event
        fields = (
            'title',
            'cover',
            'type',
            'text_src',
        )


class UserForm(RealmEditBaseForm):

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'digest_enabled',
            'comments_enabled',
            'disqus_shortname',
            'disqus_category_id',
        )
