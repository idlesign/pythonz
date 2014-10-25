from django import forms
from django.contrib.contenttypes.models import ContentType
from datetimewidget.widgets import DateTimeWidget

from ..models import Book, Video, Event, Discussion, User, Article, Community
from ..generics.forms import RealmEditBaseForm
from .widgets import RstEditWidget, ReadOnlyWidget, PlaceWidget


class DiscussionForm(RealmEditBaseForm):

    class Meta:
        model = Discussion
        fields = (
            'title',
            'text_src',
            'object_id',
            'content_type',
        )
        labels = {'text_src': ''}
        widgets = {
            'object_id': forms.HiddenInput(),
            'content_type': forms.HiddenInput(),
            'text_src': RstEditWidget(attrs={'rows': 15})
        }

    @classmethod
    def _get_realm_item(cls, realm, item_id):
        """Вернёт объект из указанной области по иднетификтаору, либо None.

        :param RealmBase realm:
        :param int item_id:
        :return:
        """
        item = None
        try:
            item = realm.model.objects.get(pk=item_id)
        except realm.model.DoesNotExist:
            pass
        return item

    def __init__(self, *args, **kwargs):
        data = args[0]

        if data and ('related_item_realm' in data and 'related_item_id' in data):
            # Вызов со страницы сущности одной из областей.
            # Связываем сущность с обсуждением.

            from ..realms import get_realm

            realm = get_realm(data['related_item_realm'])
            if realm is not None:
                item_id = data['related_item_id']
                item = self._get_realm_item(realm, item_id)

                if item is not None:
                    data = dict(data)

                    data['object_id'] = item_id
                    data['content_type'] = ContentType.objects.get_for_model(item).id

                    data['title'] = '%s про «%s»' % (kwargs['user'].get_display_name(), item.title)

                    args = list(args)
                    args[0] = data

        super().__init__(*args, **kwargs)


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
            'text_src': RstEditWidget(attrs={'rows': 25}),
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
        else:
            isbn = None
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
        from ..utils import PROJECT_SOURCE_URL  # Потакаем поведению Django 1.7 при загрузке приложений.
        url = self.cleaned_data['url']
        if not Video.get_hosting_for_url(url):
            raise forms.ValidationError('К сожалению, мы не умеем работать с этим видео-хостингом. Если знаете, как это исправить, приходите <a href="%s">сюда</a>.' % PROJECT_SOURCE_URL)
        return url

    def save(self, *args, **kwargs):
        self.instance.update_code_and_cover(self.cleaned_data['url'])
        return super().save(*args, **kwargs)


CALENDAR_OPTIONS = {
    'todayHighlight': True,
    'weekStart': 1
}


class EventForm(RealmEditBaseForm):

    class Meta:
        model = Event
        fields = (
            'title',
            'type',
            'specialization',
            'fee',
            'url',
            'time_start',
            'time_finish',
            'description',
            'cover',
            'contacts',
            'place',
            'text_src',
        )
        widgets = {
            'place': PlaceWidget(),
            'text_src': RstEditWidget(attrs={'rows': 10}),
            'time_start': DateTimeWidget(usel10n=True, options=CALENDAR_OPTIONS, bootstrap_version=3),
            'time_finish': DateTimeWidget(usel10n=True, options=CALENDAR_OPTIONS, bootstrap_version=3),
        }


class UserForm(RealmEditBaseForm):

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'url',
            'email_public',
            'digest_enabled',
            'place',
            'timezone',
            'comments_enabled',
            'disqus_shortname',
            'disqus_category_id',
        )
        widgets = {
            'place': PlaceWidget(),
            'timezone': ReadOnlyWidget(),
        }

    def save(self, commit=True):
        if 'place' in self.changed_data:
            self.instance.set_timezone_from_place()
        super().save(commit=commit)


class CommunityForm(RealmEditBaseForm):

    class Meta:
        model = Community
        fields = (
            'title',
            'url',
            'description',
            'text_src',
            'contacts',
            'place',
            'year',
        )
        widgets = {
            'place': PlaceWidget(),
            'text_src': RstEditWidget(attrs={'rows': 10})
        }

