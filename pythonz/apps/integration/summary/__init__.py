from .base import ItemsFetcherBase
from .fetchers import (
    Discuss,
    GithubTrending,
    Lwn,
    MailarchAnnounce,
    MailarchConferences,
    MailarchIdeas,
    Psf,
)
from .fetchers import (
    Stackoverflow as Stackoverflow,
)
from .fetchers import (
    StackoverflowRu as StackoverflowRu,
)

SUMMARY_FETCHERS: dict[str, type[ItemsFetcherBase]] = {fetcher.alias: fetcher for fetcher in [
    MailarchAnnounce,
    MailarchConferences,
    MailarchIdeas,
    Discuss,
    Psf,
    # Stackoverflow,  # 403 ошибка при получении csv
    # StackoverflowRu,
    GithubTrending,
    Lwn,
]}
"""Сборщики сводок, индексированные псевдонимами."""
