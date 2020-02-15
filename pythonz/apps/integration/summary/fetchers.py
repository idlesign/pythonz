from collections import defaultdict
from datetime import datetime
from typing import Tuple, List, Dict, Union, Optional

from .base import PipermailBase, StackdataBase, ItemsFetcherBase, SummaryItem, FetcherResult, HyperKittyBase
from ..utils import get_from_url, make_soup, get_json


class MailarchAnnounce(HyperKittyBase):

    title: str = 'Анонсы'
    alias: str = 'python-announce-list@python.org'


class MailarchDev(HyperKittyBase):

    title: str = 'Разработка языка'
    alias: str = 'python-dev@python.org'


class MailarchConferences(PipermailBase):

    title: str = 'Мероприятия'
    alias: str = 'conferences'


class MailarchIdeas(HyperKittyBase):

    title: str = 'Идеи'
    alias: str = 'python-ideas@python.org'


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


class Discuss(ItemsFetcherBase):
    """Получатель обсуждений от discuss.python.org."""

    title: str = 'Обсуждения'
    alias: str = 'discuss'

    url_base: str = 'https://discuss.python.org'

    def fetch(self) -> FetcherResult:

        url_digest = f'{self.url_base}/top/weekly.json'  # За неделю.
        url_topic_prefix = f'{self.url_base}/t/'

        items = {}
        result = get_json(url_digest)

        if not result:
            return

        for topic in result['topic_list']['topics']:
            item_title = topic['title']
            item_url = f"{url_topic_prefix}{topic['id']}"
            items[item_url] = SummaryItem(url=item_url, title=item_title)

        items, latest_result = self._filter(items)

        return items, latest_result


class Psf(ItemsFetcherBase):

    title: str = 'Блог PSF'
    alias: str = 'psf'

    url_base: str = 'https://discuss.python.org'

    mode_cumulative: bool = True
    mode_remove_unchanged: bool = True

    def fetch(self) -> FetcherResult:

        url_rss = 'https://pyfound.blogspot.com/feeds/posts/default?alt=rss'

        items = {}
        result = get_from_url(url_rss)
        soup = make_soup(result.text)

        for entry in soup.select('entry'):
            item_title = entry.find('title').text.strip()
            item_url = entry.find('feedburner:origlink').text.strip()
            items[item_url] = SummaryItem(url=item_url, title=item_title)

        items, latest_result = self._filter(items)

        return items, latest_result


class Lwn(ItemsFetcherBase):

    title: str = 'Материалы от LWN'
    alias: str = 'lwn'

    url_base: str = 'https://lwn.net'

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

        url_base = self.url_base

        page = get_from_url(f'{url_base}/Archives/ConferenceIndex/')
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
                    url = paragraph.select('a')[0].attrs['href']
                    by_category[category].append(
                        SummaryItem(url=f'{url_base}{url}', title=f'{category}: {title}'))

        return self._filter(by_category)


class GithubTrending(ItemsFetcherBase):
    """Сборщик данных о наиболее популярных репозиториях на GitHub."""

    title: str = 'Популярное на GitHub'
    alias: str = 'github_trending'

    url_base: str = 'https://github.com'

    mode_remove_unchanged: bool = True

    def __init__(self, *, previous_result: List, previous_dt: Optional[datetime], period=None, **kwargs):
        """

        :param previous_result:
        :param period: weekly, daily, monthly
        :param kwargs:

        """
        self.period = period or 'weekly'
        super().__init__(previous_result=previous_result, previous_dt=previous_dt, **kwargs)

    def fetch(self) -> FetcherResult:
        period = self.period

        url_base = self.url_base
        url = f'{url_base}/trending/python?since={period}'

        page = get_from_url(url)
        soup = make_soup(page.text)

        items = {}

        list_items = soup.select('article')

        for list_item in list_items:

            link = list_item.select('h1 a')[0]

            item_url = f"{url_base}{link.attrs['href']}"
            item_title = link.text.strip().replace('\n', '').replace(' ', '')

            try:
                item_description = list_item.select('p')[0].text.strip()

            except IndexError:
                item_description = ''

            items[item_url] = SummaryItem(item_url, item_title, item_description)

        items, latest_result = self._filter(items)

        return items, latest_result
