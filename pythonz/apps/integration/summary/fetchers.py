from collections import defaultdict
from typing import Tuple, List, Dict, Union

from .base import PipermailBase, StackdataBase, ItemsFetcherBase, SummaryItem, FetcherResult
from ..utils import get_from_url, make_soup


class MailarchAnnounce(PipermailBase):

    title: str = 'Анонсы'
    alias: str = 'python-announce-list'


class MailarchDev(PipermailBase):

    title: str = 'Разработка языка'
    alias: str = 'python-dev'


class MailarchConferences(PipermailBase):

    title: str = 'Мероприятия'
    alias: str = 'conferences'


class MailarchIdeas(PipermailBase):

    title: str = 'Идеи'
    alias: str = 'python-ideas'


class Stackoverflow(StackdataBase):

    title: str = 'StackOverflow'
    alias: str = 'stack-en'
    site: str = 'stackoverflow'
    domain: str = 'stackoverflow.com'
    query_revision_id: int = 851710


class StackoverflowRu(StackdataBase):

    title: str = 'StackOverflow на русском'
    alias: str = 'stack-ru'
    site: str = 'ru'
    domain: str = 'ru.stackoverflow.com'
    query_revision_id: int = 851710


class Lwn(ItemsFetcherBase):

    title: str = 'Материалы от LWN'
    alias: str = 'lwn'

    relevant_cats: dict = {
        'EuroPython',
        'PyCon',
        'Python Language Summit',
    }

    def _filter(self, items: dict) -> Tuple[List[SummaryItem], Union[List, Dict]]:

        previous_result = self.previous_result or {}
        latest_result = {}
        result = []

        for category, category_items in items.items():
            prev_latest_url = previous_result.get(category)

            if prev_latest_url:
                # Возможно найдётся новый материал в старой категории.
                # Отсекаем ранее обработанные записи.
                start_from = [item.url for item in category_items].index(prev_latest_url) + 1
                result.extend(category_items[start_from:])

            else:
                # Новая категория.
                result.extend(category_items)

            latest_result[category] = category_items[-1].url

        return result, latest_result

    def fetch(self) -> FetcherResult:

        url_base = 'https://lwn.net'

        page = get_from_url(url_base + '/Archives/ConferenceIndex/')
        soup = make_soup(page.text)

        category = ''
        relevant_cats = self.relevant_cats
        by_category = defaultdict(list)

        for paragraph in soup.select('p'):

            css = paragraph.attrs.get('class')

            if not css:
                continue

            css = css[0]

            if css == 'IndexPrimary':
                category = paragraph.select('a')[-1].text
                continue

            elif css == 'IndexEntry':
                title, _, _ = paragraph.text.strip('\n )').rpartition('(')

                is_relevant = category in relevant_cats
                is_related = 'python' in title.lower()

                if is_relevant or is_related:
                    url = url_base + paragraph.select('a')[0].attrs['href']
                    by_category[category].append(SummaryItem(url=url, title=f'{category}: {title}'))

        return self._filter(by_category)


class GithubTrending(ItemsFetcherBase):
    """Сборщик данных о наиболее популярных репозиториях на GitHub."""

    title: str = 'Популярное на GitHub'
    alias: str = 'github_trending'

    mode_remove_unchanged: bool = True

    def __init__(self, previous_result, previous_dt, period=None, **kwargs):
        """

        :param previous_result:
        :param period: weekly, daily, monthly
        :param kwargs:

        """
        self.period = period or 'weekly'
        super().__init__(previous_result, previous_dt, **kwargs)

    def fetch(self) -> FetcherResult:
        period = self.period
        url_base = 'https://github.com'
        url = url_base + '/trending/python?since=' + period

        page = get_from_url(url)
        soup = make_soup(page.text)

        items = {}

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
