from typing import Optional, List, Type, Union

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from .widgets import RstEditWidget
from ..generics.forms import RealmEditBaseForm
from ..generics.models import RealmBaseModel, CommonEntityModel
from ..generics.realms import RealmBase
from ..integration.videos import VideoBroker
from ..models import Book, Video, Event, Discussion, User, Article, Community, Reference, Version, App


class DiscussionForm(RealmEditBaseForm):

    hidden_fields = {'object_id', 'content_type'}

    class Meta(RealmEditBaseForm.Meta):

        model = Discussion
        fields = (
            'title',
            'text_src',
            'object_id',
            'content_type',
        )
        labels = {'text_src': ''}

    @classmethod
    def _get_realm_item(
            cls,
            realm: Type[RealmBase],
            item_id: int
    ) -> Optional[Union[RealmBaseModel, CommonEntityModel]]:
        """Вернёт объект из указанной области по идентификтаору, либо None.

        :param realm:
        :param item_id:

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

            if realm := get_realm(data['related_item_realm']) is not None:
                item_id = data['related_item_id']

                if item := self._get_realm_item(realm, item_id) is not None:
                    data = dict(data)

                    data['object_id'] = item_id
                    data['content_type'] = ContentType.objects.get_for_model(item).id

                    data['title'] = f"{kwargs['user'].get_display_name()} про «{item.title}»"

                    args = list(args)
                    args[0] = data

        super().__init__(*args, **kwargs)


class VersionForm(RealmEditBaseForm):

    class Composer(RealmEditBaseForm.Composer):

        attrs = {
            'text_src': {'rows': 25},
        }

    class Meta(RealmEditBaseForm.Meta):

        model = Version
        fields = (
            'title',
            'date',
            'date_till',
            'status',
            'description',
            'text_src',
        )


class ArticleForm(RealmEditBaseForm):

    class Composer(RealmEditBaseForm.Composer):

        attrs = {
            'text_src': {'rows': 25},
        }
    
    class Meta(RealmEditBaseForm.Meta):

        model = Article
        fields = (
            'title',
            'description',
            'status',
            'published_by_author',
            'text_src',
        )
        labels = {
            'description': 'Введение',
            'text_src': ''
        }
        widgets = {
            'text_src': RstEditWidget(attrs={'rows': 25}),
        }

    def set_fields_required(self, fields: List[str], required: bool = True):

        for field in fields:
            self.fields[field].required = required

    def full_clean(self):

        if self.data:

            try:
                location = self.fields['location'].clean(self.data.get('location'))

            except (forms.ValidationError, KeyError):
                pass

            else:
                if location == Article.LOCATION_INTERNAL:
                    self.data['url'] = None
                    self.set_fields_required(['url'], False)

                elif location == Article.LOCATION_EXTERNAL:
                    self.set_fields_required(['url'])
                    self.set_fields_required(['title', 'description', 'text_src'], False)

        return super().full_clean()

    def clean_url(self) -> Optional[str]:
        return self.cleaned_data['url'].strip() or None

    def save(self, *args, **kwargs):
        url = self.cleaned_data.get('url')

        if url:
            self.instance.update_data_from_url(url)

        return super().save(*args, **kwargs)


class BookForm(RealmEditBaseForm):

    class Meta(RealmEditBaseForm.Meta):

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
    def clean_isbn_(isbn) -> Optional[str]:
        isbn = isbn or ''
        isbn = isbn.replace('-', '').strip()

        if length := len(isbn):
            if (length != 10 and length != 13) or not isbn.isdigit():
                raise forms.ValidationError('Код ISBN должен содержать 10, либо 13 цифр.')

        else:
            isbn = None

        return isbn

    def clean_isbn(self) -> Optional[str]:
        return self.clean_isbn_(self.cleaned_data['isbn'])

    def clean_isbn_ebook(self) -> Optional[str]:
        return self.clean_isbn_(self.cleaned_data['isbn_ebook'])


class VideoForm(RealmEditBaseForm):

    class Meta(RealmEditBaseForm.Meta):

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
            'url': f"URL страницы с видео. Умеем работать с {', '.join(Video.get_supported_hostings())}",
        }

    def clean_url(self) -> str:
        url = self.cleaned_data['url']

        if not VideoBroker.get_hosting_for_url(url):
            raise forms.ValidationError(
                'К сожалению, мы не умеем работать с этим видео-хостингом. '
                f'Если знаете, как это исправить, приходите <a href="{settings.PROJECT_SOURCE_URL}">сюда</a>.'
            )

        return url

    def save(self, *args, **kwargs):
        self.instance.update_code_and_cover(self.cleaned_data['url'])
        return super().save(*args, **kwargs)


class EventForm(RealmEditBaseForm):

    class Meta(RealmEditBaseForm.Meta):

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


class UserForm(RealmEditBaseForm):

    readonly_fields = {'timezone'}

    class Meta(RealmEditBaseForm.Meta):

        model = User
        fields = (
            'first_name',
            'last_name',
            'profile_public',
            'place',
            'timezone',
            'url',
            'email_public',
        )

    def save(self, *args, **kwargs):

        if 'place' in self.changed_data:
            self.instance.set_timezone_from_place()

        super().save(*args, **kwargs)


class CommunityForm(RealmEditBaseForm):

    class Meta(RealmEditBaseForm.Meta):

        model = Community
        fields = (
            'title',
            'url',
            'cover',
            'description',
            'text_src',
            'contacts',
            'place',
            'year',
        )


class ReferenceForm(RealmEditBaseForm):

    class Composer(RealmEditBaseForm.Composer):

        attrs = {
            'func_params': {'rows': 4},
        }

    class Meta(RealmEditBaseForm.Meta):

        model = Reference
        fields = (
            'status',
            'type',
            'parent',
            'title',
            'description',
            'func_proto',
            'func_params',
            'func_result',
            'text_src',
            'pep',
            'version_added',
            'version_deprecated',
            'search_terms',
        )


class AppForm(RealmEditBaseForm):

    class Meta(RealmEditBaseForm.Meta):

        model = App
        fields = (
            'title',
            'slug',
            'description',
            'repo',
            'status',
            'author',
            'text_src',
        )

    def clean_slug(self) -> Union[str, None]:
        return self.cleaned_data.get('slug', '').strip() or None
