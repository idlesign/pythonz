from admirarchy.toolbox import HierarchicalModelAdmin
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.contenttypes.admin import GenericTabularInline
from simple_history.admin import SimpleHistoryAdmin

from .integration.partners import get_partners_choices
from .forms.forms import BookForm
from .models import Book, Video, Event, User, Article, Place, Community, Discussion, Reference, Version, PartnerLink, \
    Vacancy, ReferenceMissing, PEP, Person, ExternalResource, Summary


def get_inline(model, field_name):
    """Возвращает класс встраиваемого редактора для использования
    в inlines в случаях полей многие-ко-многим.

    :param model:
    :param str field_name:
    :rtype: class
    """
    inline_cls = type('%sInline' % model.__name__.capitalize, (admin.TabularInline,), {
        'model': getattr(model, field_name).through,
        'extra': 0,
    })
    return inline_cls


##################################################################################
# Делаем возможным редактировение пользователей (модель изменена нами) в административной части.
# Пользователи отобразятся в разделе текущего приложения.
# Взято из http://stackoverflow.com/a/17496836/308265


class UserChangeForm(BaseUserChangeForm):

    class Meta(BaseUserChangeForm.Meta):
        model = User


class UserCreationForm(BaseUserCreationForm):

    class Meta(BaseUserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm
    list_display = BaseUserAdmin.list_display + ('is_active',)

    fieldsets = BaseUserAdmin.fieldsets + ((None, {'fields': (
            'profile_public',
            'comments_enabled',
            'disqus_shortname',
            'disqus_category_id',
            'timezone',
            'url',
            'twitter',
            'email_public'
    )}),)

##################################################################################
# Партнёрские ссылки.
#


class PartnerLinkForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        field = self.fields['partner_alias']
        field.widget = forms.fields.Select(choices=get_partners_choices())

    class Meta:
        model = PartnerLink
        fields = '__all__'


class PartnerLinkInline(GenericTabularInline):

    model = PartnerLink
    form = PartnerLinkForm
    extra = 0


@admin.register(PartnerLink)
class PartnerLinkAdmin(admin.ModelAdmin):

    list_display = ('linked_object', 'partner_alias', 'url')
    list_filter = ['partner_alias']


##################################################################################

@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):

    list_display = ('time_created',)
    list_filter = ['time_created']


@admin.register(ExternalResource)
class ExternalResourceAdmin(admin.ModelAdmin):

    list_display = ('title', 'url', 'src_alias', 'realm_name')
    list_filter = ['src_alias', 'realm_name']
    search_fields = ['title', 'description']


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):

    list_display = ('geo_title', 'title', 'status', 'time_created')
    search_fields = ['title', 'geo_title']
    raw_id_fields = ('last_editor',)
    list_filter = ['time_created', 'status', 'geo_type']
    ordering = ['geo_title']


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):

    list_display = ('title', 'src_id', 'status', 'time_created')
    search_fields = ['title', 'src_id']
    list_filter = ['status', 'place']
    ordering = ['-time_created']


class EntityBaseAdmin(SimpleHistoryAdmin):

    list_display = ('time_created', 'title', 'submitter',)
    raw_id_fields = ['submitter', 'last_editor', 'linked']
    search_fields = ['title', 'description']
    list_filter = ['time_created', 'status']
    ordering = ['-time_created']
    readonly_fields = ['time_published', 'supporters_num']

    actions = ['publish']

    def publish(self, request, queryset):
        for obj in queryset:
            obj.mark_published()
            obj.save()

    publish.short_description = 'Опубликовать'


@admin.register(Article)
class ArticleAdmin(EntityBaseAdmin):

    list_display = ('time_created', 'title', 'submitter', 'source', 'published_by_author')
    list_filter = ['time_created', 'status', 'source', 'published_by_author']

@admin.register(Book)
class BookAdmin(EntityBaseAdmin):

    form = BookForm

    list_display = ('time_created', 'title', 'submitter', 'isbn')
    search_fields = ['title', 'isbn']
    inlines = [PartnerLinkInline]


@admin.register(Community)
class CommunityAdmin(EntityBaseAdmin):

    search_fields = ['title', 'description', 'text']


@admin.register(Discussion)
class DiscussionAdmin(EntityBaseAdmin):

    search_fields = ['title', 'description', 'text']


@admin.register(Event)
class EventAdmin(EntityBaseAdmin):

    list_display = ('time_created', 'title', 'submitter', 'type', 'specialization')
    search_fields = ['title', 'description', 'text']
    list_filter = ['time_created', 'status', 'type', 'specialization']


@admin.register(Video)
class VideoAdmin(EntityBaseAdmin): pass


@admin.register(PEP)
class PEPAdmin(EntityBaseAdmin):

    list_display = ('num', 'title', 'type', 'status')
    search_fields = ['title', 'description']
    list_filter = ['status', 'type']
    raw_id_fields = EntityBaseAdmin.raw_id_fields + ['versions', 'superseded', 'replaces', 'requires', 'linked', 'authors']
    readonly_fields = EntityBaseAdmin.readonly_fields + ['status', 'type', 'description']


@admin.register(Reference)
class ReferenceAdmin(HierarchicalModelAdmin, EntityBaseAdmin):

    hierarchy = True
    list_display = ('title', 'submitter', 'type')
    list_filter = ['time_created', 'status', 'type', 'version_added', 'version_deprecated']


@admin.register(ReferenceMissing)
class ReferenceMissingAdmin(admin.ModelAdmin):

    list_display = ('term', 'synonyms', 'hits')
    search_fields = ['term', 'synonyms']
    ordering = ['-hits', 'term']


@admin.register(Version)
class VersionAdmin(EntityBaseAdmin):

    list_display = ('title', 'current', 'status', 'slug')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):

    list_display = ('name', 'name_en', 'time_created')
    search_fields = ['name', 'name_en', 'aka']
    list_filter = ['status']
    ordering = ['name']
    raw_id_fields = ['user', 'last_editor']
    readonly_fields = ['text', 'supporters_num']
