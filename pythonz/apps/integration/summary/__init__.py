from typing import Dict, Type

from .base import ItemsFetcherBase
from .fetchers import MailarchAnnounce, MailarchConferences, MailarchDev, MailarchIdeas, \
    Stackoverflow, StackoverflowRu, GithubTrending, Lwn, Discuss

SUMMARY_FETCHERS: Dict[str, Type[ItemsFetcherBase]] = dict(((fetcher.alias, fetcher) for fetcher in [
    MailarchAnnounce,
    MailarchConferences,
    MailarchDev,
    MailarchIdeas,
    Discuss,
    Stackoverflow,
    StackoverflowRu,
    GithubTrending,
    Lwn,
]))
"""Сборщики сводок, индексированные псевдонимами."""
