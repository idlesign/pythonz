from collections import defaultdict
from enum import unique
from typing import Dict, Type, Optional, List, Set

from django.db import models

from .utils import get_from_url, PageInfo, get_page_info, run_threads


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
    def get_sources(cls) -> Dict[str, Type['RemoteSource']]:
        """Возвращает словарь с источниками, зарегистрированными для области."""
        return cls.registry[cls.realm]

    @classmethod
    def get_source(cls, alias: str) -> Optional[Type['RemoteSource']]:
        """Возвращает класс источника по псевдониму.

        :param alias: Псевдоним источника.

        """
        return cls.get_sources().get(alias)

    @classmethod
    def get_enum(cls) -> Type[models.TextChoices]:
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

    def fetch_list(self) -> List[dict]:
        """Возвращает словарь с данными записей, полученных из внешнего
        источника.

        """
        raise NotImplementedError  # pragma: nocover

    @classmethod
    def get_page_info(cls, url: str) -> Optional[PageInfo]:
        """Возвращает информацию о странице, расположенной
        по указанному адресу, либо None.

        :param url:

        """
        return get_page_info(url)

    @classmethod
    def get_pages_info(cls, urls: Set[str], *, thread_num: int = None) -> Dict[str, Optional[PageInfo]]:
        """Возвращает информацию о страницах, расположенных
        по указанным адресам. Отправляет запросы в нитях.

        :param urls:

        :param thread_num: Количество нитей для забора данных.
            Если не указано, о будет создано нитей по количеству URL,
            но не более определённого числа.

        """
        return run_threads(urls, cls.get_page_info, thread_num=thread_num)

    @classmethod
    def contribute_page_info(cls, results: List[dict]):
        """Дополняет указанные словари результатов ключем __page_info,
        в котором будут указаны данные страниц, упомянутых в ключах `url`.

        Внимание: изменяет исходный список.

        :param results:

        """
        by_url = cls.get_pages_info(set(item['url'] for item in results))

        for item in results:
            page_info = by_url.get(item['url'])
            item['__page_info'] = page_info or None
