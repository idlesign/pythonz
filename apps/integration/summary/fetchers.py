from collections import OrderedDict

from .base import PipermailBase, StackdataBase, ItemsFetcherBase, SummaryItem
from ..utils import get_from_url, make_soup


class MailarchAnnounce(PipermailBase):

    title = 'Анонсы'
    alias = 'python-announce-list'


class MailarchDev(PipermailBase):

    title = 'Разработка языка'
    alias = 'python-dev'


class MailarchConferences(PipermailBase):

    title = 'Мероприятия'
    alias = 'conferences'


class MailarchIdeas(PipermailBase):

    title = 'Идеи'
    alias = 'python-ideas'


class Stackoverflow(StackdataBase):

    title = 'StackOverflow'
    alias = 'stack-en'
    site = 'stackoverflow'
    domain = 'stackoverflow.com'
    query_revision_id = 851710


class StackoverflowRu(StackdataBase):

    title = 'StackOverflow на русском'
    alias = 'stack-ru'
    site = 'ru'
    domain = 'ru.stackoverflow.com'
    query_revision_id = 851710


class GithubTrending(ItemsFetcherBase):
    """Сборщик данных о наиболее популярных репозиториях на GitHub."""

    title = 'Популярное на GitHub'
    alias = 'github_trending'

    mode_remove_unchanged = True

    def __init__(self, previous_result, previous_dt, period=None,**kwargs):
        """

        :param previous_result:
        :param period: weekly, daily, monthly
        :param kwargs:

        :rtype: tuple
        """
        self.period = period or 'weekly'
        super().__init__(previous_result, previous_dt, **kwargs)

    def fetch(self):
        period = self.period
        url_base = 'https://github.com'
        url = url_base + '/trending/python?since=' + period

        page = get_from_url(url)
        soup = make_soup(page.text)

        items = OrderedDict()

        list_items = soup.select('ol.repo-list li')
        for list_item in list_items:
            link = list_item.select('h3 a')[0]

            item_url = url_base + link.attrs['href']
            item_title = link.text.strip()

            try:
                item_description = list_item.select('div p')[0].text.strip()
            except IndexError:
                item_description = ''

            items[item_url] = SummaryItem(item_url, item_title, item_description)

        items, latest_result = self._filter(items)

        return items, latest_result
