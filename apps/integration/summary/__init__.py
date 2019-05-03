from collections import OrderedDict

from .fetchers import MailarchAnnounce, MailarchConferences, MailarchDev, MailarchIdeas, \
    Stackoverflow, StackoverflowRu, GithubTrending, Lwn


SUMMARY_FETCHERS = OrderedDict([(fetcher.alias, fetcher) for fetcher in [
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
