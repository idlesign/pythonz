import os
import re
from uuid import uuid4

from bleach import clean
from siteflags.models import ModelWithFlag
from django.core.urlresolvers import reverse
from django.db import models
from django.conf import settings
from django.utils import timezone

from ..signals import signal_new_entity, signal_entity_published


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class ModelWithAuthorAndTranslator(models.Model):
    """Класс-примесь для моделей, требующих поля с автором и переводчиком."""

    _hint_userlink = '<br><b>[u:<ид>:<имя>]</b> формирует ссылку на профиль пользователя pythonz. Например: [u:1:идле].'

    author = models.CharField('Автор', help_text='Предпочтительно имя и фамилия. Можно указать несколько, разделяя запятыми.%s' % _hint_userlink, max_length=255)
    translator = models.CharField('Перевод', help_text='Укажите переводчиков, если материал переведён на русский с другого языка. Если переводчик неизвестен, можно указать главного редактора.%s' % _hint_userlink, max_length=255, blank=True, null=True)

    class Meta:
        abstract = True


class ModelWithCompiledText(models.Model):
    """Класс-примесь для моделей, требующих поля, содержащие тексты в rst."""

    text = models.TextField('Текст')
    text_src = models.TextField('Исходный текст')

    RE_CODE = re.compile('\.\.\s*code::\s*([^\n]+)\n\n(.+?)\n\n', re.S)
    RE_GIST = re.compile('\.\.\s*gist::\s*([^\n]+)\n', re.S)
    RE_ACCENT = re.compile('`{2}([^`.,]+)`{2}')
    RE_QUOTE = re.compile('`{3}\n*([^`]+)\n*`{3}')
    RE_BOLD = re.compile('\*{2}([^*.]+)\*{2}')
    RE_ITALIC = re.compile('\*([^*.]+)\*')
    RE_URL = re.compile('(http[^\s\)]+)')

    class Meta:
        abstract = True

    @classmethod
    def compile_text(cls, text):
        """Преобразует rst-подобное форматичрование в html.

        :param text:
        :return:
        """
        from ..utils import url_mangle
        href_replacer = lambda match: '<a href="%s" target="_blank">%s</a>' % (match.group(1), url_mangle(match.group(1)))

        text = clean(text, strip=True)
        text = text.replace('\r\n', '\n')
        text = re.sub(cls.RE_BOLD, '<b>\g<1></b>', text)
        text = re.sub(cls.RE_ITALIC, '<i>\g<1></i>', text)
        text = re.sub(cls.RE_URL, href_replacer, text)
        text = re.sub(cls.RE_QUOTE, '<blockquote>\g<1></blockquote>', text)
        text = re.sub(cls.RE_ACCENT, '<code>\g<1></code>', text)
        text = re.sub(cls.RE_CODE, '<pre><code class="\g<1>">\n\g<2>\n</code></pre>\n', text)
        text = re.sub(cls.RE_GIST, '<script src="https://gist.github.com/\g<1>.js"></script>', text)

        text = text.replace('\n', '<br>')
        return text

    def save(self, *args, **kwargs):
        self.text = self.compile_text(self.text_src)
        super().save(*args, **kwargs)


def get_upload_to(instance, filename):
    """Вычисляет директорию, в которую будет загружена обложка сущности.

    :param instance:
    :param filename:
    :return:
    """
    category = getattr(instance, 'COVER_UPLOAD_TO')
    return os.path.join('img', category, 'orig', '%s%s' % (uuid4(), os.path.splitext(filename)[-1]))


class CommonEntityModel(models.Model):
    """Базовый класс для моделей сущностей."""

    COVER_UPLOAD_TO = 'common'  # Имя категории (оно же имя директории) для хранения загруженных обложек.

    title = models.CharField('Название', max_length=255, unique=True)
    description = models.TextField('Описание', blank=False, null=False)
    submitter = models.ForeignKey(USER_MODEL, related_name='%(class)s_submitters', verbose_name='Добавил')
    linked = models.ManyToManyField('self', verbose_name='Связанные объекты', help_text='Выберите объекты, имеющие отношение к данному.', blank=True)
    cover = models.ImageField('Обложка', max_length=255, upload_to=get_upload_to, null=True, blank=True)
    year = models.CharField('Год', max_length=10, null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Перекрыт, чтобы привести заголовок в порядок.

        :param args:
        :param kwargs:
        :return:
        """
        self.title = self.title.strip()
        super().save(*args, **kwargs)

    def update_cover_from_url(self, url):
        """Забирает обложку с указанного URL.

        :param url:
        :return:
        """
        from ..utils import get_image_from_url  # Потакаем поведению Django 1.7 при загрузке приложений.
        img = get_image_from_url(url)
        self.cover.save(img.name, img, save=False)

    @classmethod
    def get_paginator_objects(cls):
        """Возвращает выборку объектов для постраничной навигации.
        Должен быть реализован наследниками.

        :return:
        """
        raise NotImplementedError()

    def __unicode__(self):
        return self.title


class RealmBaseModel(ModelWithFlag):
    """Базовый класс для моделей, использующихся в областях (realms) сайта."""

    STATUS_DRAFT = 1
    STATUS_PUBLISHED = 2
    STATUS_DELETED = 3

    STATUSES = (
        (STATUS_DRAFT, 'Черновик'),
        (STATUS_PUBLISHED, 'Опубликован'),
        (STATUS_DELETED, 'Удален'),
    )

    FLAG_STATUS_BOOKMARK = 1  # Фильтр флагов-закладок.
    FLAG_STATUS_SUPPORT = 2  # Фильтр флагов-голосов-поддержки.

    time_created = models.DateTimeField('Дата создания', auto_now_add=True, editable=False)
    time_published = models.DateTimeField('Дата публикации', null=True, editable=False)
    time_modified = models.DateTimeField('Дата редактирования', null=True, editable=False)
    status = models.PositiveIntegerField('Статус', choices=STATUSES, default=STATUS_DRAFT)
    supporters_num = models.PositiveIntegerField('Количество поддержавших', default=0)

    class Meta:
        abstract = True

    realm = None  # Во время исполнения здесь будет объект области (Realm).
    items_per_page = 15  # Количество объектов для вывода на страницах списков.
    edit_form = None  # Во время исполнения здесь будет форма редактирования.

    def mark_unmodified(self):
        """Используется для того, чтобы при следующем вызове save()
        объекта он не считался изменённым.

        :return:
        """
        self._consider_modified = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._consider_modified = True  # Указывает на то, нужно ли при сохранении устанавливать время изменения
        self._status_backup = self.status

    def save(self, *args, **kwargs):
        """Перекрыт, чтобы можно было отследить флаг модифицированности объекта
        и выставить время модификации соответствующим образом.

        :param args:
        :param kwargs:
        :return:
        """
        initial_pk = self.pk
        just_published = False

        if self._status_backup != self.status:
            self._consider_modified = False  # Если сохраняем с переходом статуса, наивно полагаем объект немодифицированным.
            if self.status == self.STATUS_PUBLISHED:
                setattr(self, 'time_published', timezone.now())
                just_published = True

        if self._consider_modified:
            setattr(self, 'time_modified', timezone.now())
        else:
            self._consider_modified = True
        super().save(*args, **kwargs)

        try:
            if not initial_pk and self.pk:
                signal_new_entity.send(self.__class__, entity=self)
        except AttributeError:
            pass  # Пропускаем модели, в которых нет нужных атрибутов.

        try:
            if just_published:
                signal_entity_published.send(self.__class__, entity=self)
        except AttributeError:
            pass  # Пропускаем модели, в которых нет нужных атрибутов.

    @classmethod
    def get_actual(cls):
        """Возвращает выборку актуальных объектов.

        :return:
        """
        return cls.objects.filter(status=cls.STATUS_PUBLISHED).order_by('-time_published').all()

    @classmethod
    def get_paginator_objects(cls):
        """Возвращает выборку для постраничной навигации.

        :return:
        """
        return cls.objects.select_related('submitter').filter(status=cls.STATUS_PUBLISHED).order_by('-supporters_num', '-time_created').all()

    def get_linked(self):
        """Возвращает связанные объекты.

        :return:
        """
        return self.linked.filter(status=self.STATUS_PUBLISHED).all()

    def is_supported_by(self, user):
        """Возвращает указание на то, поддерживает ли данный пользователь данную сущность.

        :param user:
        :return:
        """
        return self.is_flagged(user, status=self.FLAG_STATUS_SUPPORT)

    def set_support(self, user):
        """Устанавливает флаг поддержки данным пользователем данной сущности.

        :param user:
        :return:
        """
        self.supporters_num += 1
        self.set_flag(user, status=self.FLAG_STATUS_SUPPORT)
        self.mark_unmodified()
        self.save()

    def remove_support(self, user):
        """Убирает флаг поддержки данным пользователем данной сущности.

        :param user:
        :return:
        """
        self.supporters_num -= 1
        self.remove_flag(user, status=self.FLAG_STATUS_SUPPORT)
        self.mark_unmodified()
        self.save()

    def get_suppport_for_objects(self, objects_list, user):
        """Возвращает данные о поддержке пользователем(ями) указанного набора сущностей.

        :param objects_list:
        :param user:
        :return:
        """
        return self.get_flags_for_objects(objects_list, user=user)

    def is_bookmarked_by(self, user):
        """Возвращает указание на то, добавил ли данный пользователь данную сущность в избранное.

        :param user:
        :return:
        """
        return self.is_flagged(user, status=self.FLAG_STATUS_BOOKMARK)

    def set_bookmark(self, user):
        """Добавляет данную сущность в избранные для данного пользователя.

        :param user:
        :return:
        """
        self.set_flag(user, status=self.FLAG_STATUS_BOOKMARK)

    def remove_bookmark(self, user):
        """Убирает данную сущность из избранного данного пользователя.

        :param user:
        :return:
        """
        self.remove_flag(user, status=self.FLAG_STATUS_BOOKMARK)

    @classmethod
    def get_verbose_name(cls):
        """Возвращает человекоудобное название типа объекта в ед. числе.

        :return:
        """
        return cls._meta.verbose_name

    @classmethod
    def get_verbose_name_plural(cls):
        """Возвращает человекоудобное название типа объекта во мн. числе.

        :return:
        """
        return cls._meta.verbose_name_plural

    def get_listing_url(self):
        """Возвращает URL страницы со списком объектов.

        :return:
        """
        tmp, realm_name_plural = self.realm.get_names()
        return reverse('%s:listing' % realm_name_plural)

    def get_absolute_url(self):
        """Возвращает URL страницы с детальной информацией об объекте.

        :return:
        """
        tmp, realm_name_plural = self.realm.get_names()
        return reverse('%s:details' % realm_name_plural, args=[str(self.id)])

    def get_category_absolute_url(self, category):
        """Возвращает URL страницы с разбивкой по данной категории.

        :param category:
        :return:
        """
        tmp, realm_name_plural = self.realm.get_names()
        return reverse('%s:tags' % realm_name_plural, args=[str(category.id)])
