from collections import defaultdict
from enum import unique

from django.db import models

from .utils import PageInfo, get_from_url, get_page_info, run_threads


class RemoteSource:
    """База для удалённых источников данных."""

    realm: str = ''
    """Область, к которой привязан источник."""

    active: bool = True
    """Показатель активности источника."""

    alias: str = ''
    """Псевдоним источника (краткий лат.)."""

    title: str = ''
    """Название источника."""

    registry: dict = defaultdict(dict)
    """Зарегистрированные источники."""

    def __init_subclass__(cls):
        super().__init_subclass__()

        alias = cls.alias

        if alias:
            cls.registry[cls.realm][alias] = cls

    @classmethod
    def get_sources(cls) -> dict[str, type['RemoteSource']]:
        """Возвращает словарь с источниками, зарегистрированными для области."""
        return cls.registry[cls.realm]

    @classmethod
    def get_source(cls, alias: str) -> type['RemoteSource'] | None:
        """Возвращает класс источника по псевдониму.

        :param alias: Псевдоним источника.

        """
        return cls.get_sources().get(alias)

    @classmethod
    def get_enum(cls) -> type[models.TextChoices]:
        """Возвращает перечисление источников для модели."""

        enum = unique(models.TextChoices('Source', [
            (alias, (alias, source_cls.title))
            for alias, source_cls in cls.get_sources().items()
        ]))

        return enum

    def request(self, url: str) -> str:
        """Отправляет запрос на указанный URL.

        :param url:

        """
        response = get_from_url(url)

        return response.text

    def fetch_list(self) -> list[dict]:
        """Возвращает словарь с данными записей, полученных из внешнего
        источника.

        """
        raise NotImplementedError  # pragma: nocover

    @classmethod
    def get_page_info(cls, url: str) -> PageInfo | None:
        """Возвращает информацию о странице, расположенной
        по указанному адресу, либо None.

        :param url:

        """
        return get_page_info(url)

    @classmethod
    def get_pages_info(cls, urls: set[str], *, thread_num: int = None) -> dict[str, PageInfo | None]:
        """Возвращает информацию о страницах, расположенных
        по указанным адресам. Отправляет запросы в нитях.

        :param urls:

        :param thread_num: Количество нитей для забора данных.
            Если не указано, о будет создано нитей по количеству URL,
            но не более определённого числа.

        """
        return run_threads(urls, cls.get_page_info, thread_num=thread_num)

    @classmethod
    def contribute_page_info(cls, results: list[dict]):
        """Дополняет указанные словари результатов ключем __page_info,
        в котором будут указаны данные страниц, упомянутых в ключах `url`.

        Внимание: изменяет исходный список.

        :param results:

        """
        by_url = cls.get_pages_info({item['url'] for item in results})

        for item in results:
            page_info = by_url.get(item['url'])
            item['__page_info'] = page_info or None
