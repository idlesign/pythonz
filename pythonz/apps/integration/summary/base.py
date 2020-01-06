import csv
import json
import re
from io import StringIO
from datetime import datetime
from collections import OrderedDict
from traceback import format_exc

import attr

from ...exceptions import LogicError
from ...signals import sig_integration_failed
from ...utils import get_logger, get_datetime_from_till
from ..utils import get_from_url, make_soup


LOG = get_logger(__name__)


@attr.s(slots=True, frozen=True)
class SummaryItem:
    """Элемент сводки."""

    url = attr.ib()
    title = attr.ib()
    description = attr.ib(default='')

    def to_json(self):
        """Представляет объект в виде json.

        :rtype: str
        """
        return json.dumps(attr.asdict(self))


class ItemsFetcherBase:
    """Базовый класс для сборщиков данных из внешних ресурсов."""

    title = None
    """Название сводки."""

    alias = None
    """Псевдоним сводки. Однажды установленный не должен оставаться неизменным."""

    mode_cumulative = False
    """Режим для работы с ресурсами, данные которых кумулятивны 
    (дополняются новые к имеющимся старым). В этом режиме все старые 
    данные будут отсеяны.

    """

    mode_remove_unchanged = False
    """Режим, при котором элементы из старого забора исключаются из нового даже если
    присутствуют в нём.

    """

    def __init__(self, previous_result, previous_dt, **kwargs):
        """

        :param list previous_result: Результат предыдущего забора данных.
        :param datetime previous_dt: Дата и время предыдущего забора данных.

        :param kwargs:

        """
        self.previous_result = previous_result or []
        self.previous_dt = previous_dt or get_datetime_from_till(7)[0]

    def run(self):
        """Основной рабочий метод. Запускает сбор данных

        :rtype: tuple[list, list]
        """
        fetcher_name = self.__class__.__name__

        LOG.debug('Summary fetcher `%s` started ...', fetcher_name)

        try:
            fetched = self.fetch()

            LOG.debug('... finished')

            return fetched

        except Exception as e:
            sig_integration_failed.send(
                None,
                description='Summary fetcher `%s` error: %s %s' % (fetcher_name, e, format_exc()))

            LOG.exception('Summary fetcher `%s` failed', fetcher_name)

        return None

    def fetch(self):
        """Забирает данные для последующей сборки в сводку.

        Должен реализовываться наследниками.

        :return: Кортеж вида:
            (список_SummaryItem, список_результов)

            Результат будет передан в previous_result при следующем заборе данных.

        :rtype: tuple[list, list]
        """
        raise NotImplementedError('`%s` must implement .fetch()' % self.__class__.__name__)  # pragma: nocover

    def _filter(self, items):
        """

        :param OrderedDict items:
        :rtype: tuple[list, list]
        """
        previous_result = self.previous_result
        mode_cumulative = self.mode_cumulative
        mode_remove_unchanged = self.mode_remove_unchanged

        idx_prev = -1

        if previous_result:

            if mode_cumulative:
                if len(previous_result) > 1:
                    raise LogicError(
                        '`%s`fetcher uses `mode_cumulative` but `previous_result` contains more than one item.' %
                        self.__class__)

                previous_result = previous_result[0]
                try:
                    idx_prev = list(items.keys()).index(previous_result)

                except ValueError:
                    pass

        new_result = []
        by_title = OrderedDict()
        for idx_current, (key, summary_item) in enumerate(items.items()):  # type: SummaryItem

            if mode_cumulative:
                if idx_current <= idx_prev:
                    continue

            elif mode_remove_unchanged:
                if key in previous_result:
                    continue

            by_title.setdefault(summary_item.title, summary_item)

            new_result.append(key)

        if mode_cumulative:
            new_result = new_result[-1:]  # Необходима и достаточна только одна строка

        return list(by_title.values()), new_result


class PipermailBase(ItemsFetcherBase):
    """Базовый сборщик данных из архивов почтовых рассылок pipermail с mail.python.org"""

    mode_cumulative = True

    def get_url(self):
        return 'https://mail.python.org/pipermail/%s/' % self.alias

    def __init__(self, previous_result, previous_dt, year_month=None, **kwargs):
        self.year_month = year_month
        super().__init__(previous_result, previous_dt, **kwargs)

    def fetch(self):
        url = self.get_url()
        year_month = self.year_month

        details_page_file = '/date.html'
        if not year_month:
            page = get_from_url(url)

            match = re.search('="((\d{4}-[^/]+)%s)"' % details_page_file, page.text)

            if not match:
                sig_integration_failed.send(None, description='Subject page link not found at %s' % url)
                return

            year_month = match.group(2)

        page = get_from_url(url + year_month + details_page_file)
        soup = make_soup(page.text)

        items = OrderedDict()

        prefix_re = re.compile('\[[^]]+\]\s*')

        list_items = soup.select('ul')[1].select('li')
        for list_item in list_items:
            link = list_item.select('a')[0]
            item_url = url + year_month + '/' + link.attrs['href']
            item_title = link.text.strip()

            # Отсекаем префикст рассылки вида `[Префикс] Тема`
            item_title = prefix_re.sub('', item_title)

            items[item_url] = SummaryItem(url=item_url, title=item_title)

        items, latest_result = self._filter(items)

        return items, latest_result


class StackdataBase(ItemsFetcherBase):
    """Базовый сборщик данных из data.stackexchange.com.
    Данные обновляются каждое воскресенье.

    """

    site = None
    domain = None
    query_revision_id = None

    def __init__(self, previous_result, previous_dt, top_count=10, **kwargs):
        self.top_count = top_count
        super().__init__(previous_result, previous_dt, **kwargs)

    def get_url(self):
        since = self.previous_dt.strftime('%Y%m%d')
        url = (
            'http://data.stackexchange.com/%(site)s/csv/%(revision_id)s?top=%(top)s&since=%(since)s' % {
                'site': self.site,
                'revision_id': self.query_revision_id,
                'top': self.top_count,
                'since': since,
            }
        )
        return url

    def get_item_url(self, item_id):
        return 'https://%s/questions/%s/' % (self.domain, item_id)

    def fetch(self):
        url = self.get_url()
        response = get_from_url(url)

        items = OrderedDict()

        reader = csv.DictReader(StringIO(response.text))
        for row in reader:
            item_id = row['id']
            item_url = self.get_item_url(item_id)
            item_title = row['Title']
            items[item_id] = SummaryItem(item_url, item_title)

        items, latest_result = self._filter(items)

        return items, latest_result
