from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from etc.models import InheritedModel
from simple_history.models import HistoricalRecords
from sitecats.models import ModelWithCategory

from ..generics.models import CommonEntityModel, ModelWithCompiledText, RealmBaseModel
from ..utils import truncate_chars


class Discussion(InheritedModel, RealmBaseModel, CommonEntityModel, ModelWithCategory, ModelWithCompiledText):
    """Модель обсуждений. Пользователи могут обсудить желаемые темы и привязать обсужедние к сущности на сайте.
    Фактически - форум.
    
    """
    object_id = models.PositiveIntegerField(verbose_name='ID объекта', db_index=True, null=True, blank=True)

    content_type = models.ForeignKey(
        ContentType, verbose_name='Тип содержимого', related_name='%(class)s_discussions', null=True, blank=True,
        on_delete=models.SET_NULL)

    linked_object = GenericForeignKey()

    history = HistoricalRecords()

    class Meta:

        verbose_name = 'Обсуждение'
        verbose_name_plural = 'Обсуждения'

    class Fields:

        text = 'Обсуждение'

    def save(self, *args, **kwargs):

        if not self.pk:
            self.mark_published()

        super().save(*args, **kwargs)

    def get_description(self) -> str:
        return truncate_chars(self.text, 360, html=True)


class ModelWithDiscussions(models.Model):
    """Класс-примесь к моделям сущностей, для который разрешено оставление мнений."""

    discussions = GenericRelation(Discussion)

    class Meta:

        abstract = True
