from typing import Dict, List

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import FieldError
from django.db import models
from django.db.models import QuerySet
from siteflags.utils import get_flag_model

from .category import Category
from .place import Place
from .shared import UtmReady
from ..generics.models import RealmBaseModel
from ..integration.utils import get_timezone_name


class User(UtmReady, RealmBaseModel, AbstractUser):
    """Наша модель пользователей."""

    allow_edit_anybody: bool = False
    items_per_page: int = 14
    details_related: List[str] = ['last_editor', 'person', 'place']

    objects = UserManager()

    place = models.ForeignKey(
        Place, verbose_name='Место', related_name='users', null=True, blank=True,
        help_text='Место вашего пребывания (страна, город, село).<br>'
                  'Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».',
        on_delete=models.SET_NULL)

    profile_public = models.BooleanField(
        'Публичный профиль', default=True, db_index=True,
        help_text='Если выключить, то увидеть ваш профиль сможете только вы.<br>'
                  'В списках пользователей профиль значиться тоже не будет.')

    comments_enabled = models.BooleanField(
        'Разрешить комментарии',
        help_text='Включает/отключает систему комментирования Disqus на страницах ваших публикаций.', default=False)

    disqus_shortname = models.CharField(
        'Идентификатор Disqus', max_length=100, null=True, blank=True,
        help_text='Короткое имя (shortname), под которым вы зарегистрировали форум на Disqus.')

    disqus_category_id = models.CharField(
        'Идентификатор категории Disqus', max_length=30, null=True, blank=True,
        help_text='Если ваш форум на Disqus использует категории, можете указать нужный номер здесь. '
                  'Это не обязательно.')

    timezone = models.CharField(
        'Часовой пояс', max_length=150, null=True, blank=True,
        help_text='Название часового пояса. Например: Asia/Novosibirsk.<br>'
                  '* Устанавливается автоматически в зависимости от места пребывания (см. выше).')

    email_public = models.EmailField(
        'Эл. почта', null=True, blank=True,
        help_text='Адрес электронной почты для показа посетителям сайта.')

    twitter = models.CharField(
        'Twitter', max_length=100, blank=True, default='',
        help_text='Имя в Twitter.')

    url = models.URLField('Страница в сети', null=True, blank=True)

    karma = models.DecimalField('Карма', max_digits=6, decimal_places=2, default=0)

    class Meta:

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.get_full_name() or self.get_username_partial()

    @property
    def title(self) -> str:
        return self.get_display_name()

    @property
    def is_draft(self) -> bool:
        # Не считаем черновиком, считаем опубликованным.
        return False

    def set_timezone_from_place(self):
        """Устанавливает временную зону, исходя из места расположения."""

        if self.place is None:
            self.timezone = None
            return True

        geo_pos = self.place.geo_pos

        if geo_pos:
            lat, lng = geo_pos.split(',')
            self.timezone = get_timezone_name(lat, lng)

    def get_drafts(self) -> Dict[str, QuerySet]:
        """Возвращает словарь с неопубликованными материалами пользователя.
        Индексирован названиями разделов сайта; значения — списки материалов.

        """
        from ..realms import get_realms_models

        drafts = {}

        for realm_model in get_realms_models():

            try:
                realm_name = realm_model.get_verbose_name_plural()

            except AttributeError:
                pass

            else:
                items = realm_model.objects.filter(
                    status__in=(self.Status.DRAFT, self.Status.POSTPONED),
                    submitter_id=self.id

                ).order_by('time_created')

                if items:
                    drafts[realm_name] = items

        return drafts

    def get_stats(self) -> Dict[str, Dict]:
        """Возвращает словарь со статистикой пользователя.

        Индексирован названиями разделов сайта; значения — словарь со статистикой:
            cnt_published - кол-во опубликованных материалов
            cnt_postponed - кол-во материалов, назначенных к отложенной публикации

        """
        from ..realms import get_realms_models

        stats = {}
        for realm_model in get_realms_models():

            try:
                realm_name = realm_model.get_verbose_name_plural()
                cnt_published = realm_model.objects.published().filter(submitter_id=self.id).count()
                cnt_postponed = realm_model.objects.postponed().filter(submitter_id=self.id).count()

            except (FieldError, AttributeError):
                pass

            else:

                if cnt_published or cnt_postponed:
                    stats[realm_name] = {
                        'cnt_published': cnt_published,
                        'cnt_postponed': cnt_postponed,
                    }

        return stats

    def get_bookmarks(self) -> Dict[str, QuerySet]:
        """Возвращает словарь с избранными пользователем элементами (закладками).
        Словарь индексирован классами моделей различных сущностей, в значениях - списки с самими сущностями.

        """
        from ..realms import get_realms_models

        FLAG_MODEL = get_flag_model()

        bookmarks = FLAG_MODEL.get_flags_for_types(
            get_realms_models(), user=self, status=RealmBaseModel.FLAG_STATUS_BOOKMARK,
            allow_empty=False
        )

        for realm_model, flags in bookmarks.items():
            ids = [flag.object_id for flag in flags]
            items = realm_model.objects.filter(id__in=ids)
            bookmarks[realm_model] = items

        return bookmarks

    @property
    def is_deleted(self) -> bool:
        return not self.is_active

    @classmethod
    def get_actual(cls) -> QuerySet:
        return cls.objects.filter(is_active=True, profile_public=True).order_by('-date_joined').all()

    @classmethod
    def get_paginator_objects(cls) -> QuerySet:
        return cls.get_actual()

    @classmethod
    def get_most_voted_objects(cls, category: Category = None, base_query: QuerySet = None) -> QuerySet:
        query = cls.objects.filter(supporters_num__gt=0)
        query = query.select_related('submitter').order_by('-supporters_num')
        return query.all()[:5]

    def get_username_partial(self) -> str:
        return self.username.split('@')[0]

    def get_description(self) -> str:
        """Возвращает вычисляемое описание объекта.
        Обычно должен использоваться вместо обращения к атрибуту description,
        которого может не сущестовать у модели.

        """
        return self.get_display_name()
