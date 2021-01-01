from typing import List

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

    @classmethod
    def partner_links_enrich(cls, data: dict) -> List[PartnerLink]:
        """Пополняет партнёрские ссылки по данным из указанного словаря.
        Возвращает список добавленных новых ссылок.

        :param data:

        """
        content_type = ContentType.objects.get_for_model(cls, for_concrete_model=False)

        result = []

        for title, links in data.items():

            try:
                source_obj = cls.objects.get(title=title)

            except cls.DoesNotExist:
                # Нет полного совпадения.
                # Пробуем сориентироваться по ссылкам.
                source_obj = PartnerLink.objects.filter(url__in=links).first()

                if source_obj:
                    source_obj = source_obj.linked_object

                else:
                    source_obj = cls.objects.create(title=title)

            for url, partner_alias in links.items():

                link, link_created = PartnerLink.objects.get_or_create(
                    content_type=content_type,
                    object_id=source_obj.id,
                    partner_alias=partner_alias,
                    url=url,
                )

                if link_created:
                    result.append(link)

        return result
