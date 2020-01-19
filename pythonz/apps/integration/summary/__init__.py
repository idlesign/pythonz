from collections import OrderedDict
from typing import Dict, Type

from .base import ItemsFetcherBase
from .fetchers import MailarchAnnounce, MailarchConferences, MailarchDev, MailarchIdeas, \
    Stackoverflow, StackoverflowRu, GithubTrending, Lwn

SUMMARY_FETCHERS: Dict[str, Type[ItemsFetcherBase]] = OrderedDict([(fetcher.alias, fetcher) for fetcher in [
    MailarchAnnounce,
    MailarchConferences,
    MailarchDev,
    MailarchIdeas,
    Stackoverflow,
    StackoverflowRu,
    GithubTrending,
    Lwn,
]])
"""Сборщики сводок, индексированные псевдонимами."""
