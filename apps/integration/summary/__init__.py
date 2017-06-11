from collections import OrderedDict

from .fetchers import MailarchAnnounce, MailarchConferences, MailarchDev, MailarchIdeas, \
    Stackoverflow, StackoverflowRu, GithubTrending


SUMMARY_FETCHERS = OrderedDict([(fetcher.alias, fetcher) for fetcher in [
    MailarchAnnounce,
    MailarchConferences,
    MailarchDev,
    MailarchIdeas,
    Stackoverflow,
    StackoverflowRu,
    GithubTrending,
]])
"""Сборщики сводок, индексированные псевдонимами."""
