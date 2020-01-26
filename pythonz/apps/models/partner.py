from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


class PartnerLink(models.Model):
    """Модель партнёрских ссылок. Ссылки могут быть привязаны к любым сущностям сайта.
    Логику формирования и отображения ссылок предоставляют классы из модуля partners.

    """
    object_id = models.PositiveIntegerField(verbose_name='ID объекта', db_index=True)

    content_type = models.ForeignKey(
        ContentType, verbose_name='Тип содержимого', related_name='%(class)s_partner_links',
        on_delete=models.CASCADE)

    partner_alias = models.CharField('Идентфикатор класса партнёра', max_length=50, db_index=True)

    url = models.URLField(
        'Базовая ссылка',
        help_text='Ссылка на партнёрскую страницу без указания партнёрских данных (идентификатора).')

    description = models.CharField('Описание', max_length=255, null=True, blank=True)

    linked_object = GenericForeignKey()

    class Meta:

        verbose_name = 'Партнёрская ссылка'
        verbose_name_plural = 'Партнёрские ссылки'

    def __str__(self):
        return f'Ссылка {self.id} для {self.content_type} {self.object_id}'


class ModelWithPartnerLinks(models.Model):
    """Класс-примесь к моделям сущностей, для который разрешено добавление партнёрских ссылок."""

    partner_links = GenericRelation(PartnerLink)

    class Meta:

        abstract = True
