from .base import ItemsFetcherBase
from .fetchers import (
    Discuss,
    GithubTrending,
    Lwn,
    MailarchAnnounce,
    MailarchConferences,
    MailarchIdeas,
    Psf,
    Stackoverflow,
    StackoverflowRu,
)

SUMMARY_FETCHERS: dict[str, type[ItemsFetcherBase]] = {fetcher.alias: fetcher for fetcher in [
    MailarchAnnounce,
    MailarchConferences,
    MailarchIdeas,
    Discuss,
    Psf,
    Stackoverflow,
    StackoverflowRu,
    GithubTrending,
    Lwn,
]}
"""Сборщики сводок, индексированные псевдонимами."""
