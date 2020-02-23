import csv
import json
import re
from datetime import datetime, timedelta
from io import StringIO
from traceback import format_exc
from typing import List, Tuple, Optional, Union, Dict

import attr

from ..utils import get_from_url, make_soup
from ...exceptions import LogicError
from ...signals import sig_integration_failed
from ...utils import get_logger, get_datetime_from_till

LOG = get_logger(__name__)


@attr.s(slots=True, frozen=True)
class SummaryItem:
    """Элемент сводки."""

    url = attr.ib()
    title = attr.ib()
    description = attr.ib(default='')

    def to_json(self) -> str:
        """Представляет объект в виде json."""
        return json.dumps(attr.asdict(self))


TypeFetcherResult = Optional[Tuple[List[SummaryItem], Union[List, Dict]]]


class ItemsFetcherBase:
    """Базовый класс для сборщиков данных из внешних ресурсов."""

    title: str = None
    """Название сводки."""

    alias: str = None
    """Псевдоним сводки. Однажды установленный не должен оставаться неизменным."""

    filter_cumulative: bool = False
    """Режим для работы с ресурсами, данные которых кумулятивны 
    (дополняются новые к имеющимся старым). В этом режиме все старые 
    данные будут отсеяны и останется единственный результат.

    """

    filter_skip_unchanged: bool = False
    """Режим, при котором элементы старого забора исключаются из нового, если
    присутствуют в нём.

    """

    filter_hide_seen = False
    """Убирать ли из представления элементы присутствующие и в предыдущем, и в текущем заборах."""

    def __init__(self, *, previous_result: Union[List, Dict], previous_dt: Optional[datetime], **kwargs):
        """

        :param previous_result: Результат предыдущего забора данных.
        :param previous_dt: Дата и время предыдущего забора данных.
        :param kwargs:

        """
        assert not all((self.filter_cumulative, self.filter_skip_unchanged)), (
            'Указаны взимоисключающие режимы фильтрации данных')

        self.previous_result = previous_result or []
        self.previous_dt = previous_dt or get_datetime_from_till(7)[0]

    def run(self) -> TypeFetcherResult:
        """Основной рабочий метод. Запускает сбор данных."""
        fetcher_name = self.__class__.__name__

        LOG.debug(f'Summary fetcher `{fetcher_name}` started ...')

        try:
            fetched = self.fetch()

            LOG.debug('... finished')

            return fetched

        except Exception as e:

            sig_integration_failed.send(
                None,
                description=f'Summary fetcher `{fetcher_name}` error: {e} {format_exc()}')

            LOG.exception(f'Summary fetcher `{fetcher_name}` failed')

        return None

    def fetch(self) -> TypeFetcherResult:
        """Забирает данные для последующей сборки в сводку.

        Должен реализовываться наследниками.

        Возвращает кортеж вида:
            (список_SummaryItem, результ)

            Результат используется для восставноления состояния забора
            и будет передан в previous_result при следующем заборе данных.

        """
        raise NotImplementedError(f'`{self.__class__.__name__}` must implement .fetch()')  # pragma: nocover

    def _filter(self, items: dict) -> Tuple[List[SummaryItem], Union[List, Dict]]:
        """
        :param items:

        """
        result_old = self.previous_result

        flt_cumulative = self.filter_cumulative
        flt_skip_unchanged = self.filter_skip_unchanged
        flt_hide_seen = self.filter_hide_seen

        idx_prev = -1

        if result_old:

            if flt_cumulative:

                if len(result_old) > 1:
                    raise LogicError(
                        f'`{self.__class__}`fetcher uses `mode_cumulative` '
                        'but `previous_result` contains more than one item.')

                result_old = result_old[0]

                try:
                    idx_prev = list(items.keys()).index(result_old)

                except ValueError:
                    pass

        result_new = []
        by_title = {}

        for idx_current, (key, summary_item) in enumerate(items.items()):

            summary_item: SummaryItem

            seen = key in result_old

            if flt_cumulative and idx_current <= idx_prev:
                continue

            elif flt_skip_unchanged and seen:
                continue

            if not seen or not flt_hide_seen:
                by_title.setdefault(summary_item.title, summary_item)

            result_new.append(key)

        if flt_cumulative:
            # Необходима и достаточна только одна запись
            result_new = result_new[-1:]

        return list(by_title.values()), result_new


class HyperKittyBase(ItemsFetcherBase):
    """Базовый сборщик данных из архивов почтовых рассылок
    HyperKitty (Mailman 3) с mail.python.org.

    """
    url_base: str = 'https://mail.python.org'

    def __init__(
            self,
            *,
            previous_result: List,
            previous_dt: Optional[datetime],
            till: Optional[datetime] = None,
            **kwargs
    ):
        self.till = till
        super().__init__(previous_result=previous_result, previous_dt=previous_dt, **kwargs)

    def get_url(self, *, date: datetime) -> str:
        return f"{self.url_base}/archives/list/{self.alias}/{date.strftime('%Y/%m/%d/')}"

    def fetch(self) -> TypeFetcherResult:

        since = self.previous_dt
        till = self.till or datetime.now()

        if not since:
            since = till

        delta = till.date() - since.date()
        target_dates = [till - timedelta(days=day_num) for day_num in range(0, delta.days)] or [till]

        items = {}
        url_base = self.url_base

        for target_date in target_dates:
            url = self.get_url(date=target_date)
            response = get_from_url(url)
            soup = make_soup(response.text)

            for link in soup.select('.thread-title a'):
                item_url = f"{url_base}{link.attrs['href']}"
                item_title = link.text.strip()
                items[item_url] = SummaryItem(url=item_url, title=item_title)

        items, latest_result = self._filter(items)

        return items, latest_result


class PipermailBase(ItemsFetcherBase):
    """Базовый сборщик данных из архивов почтовых рассылок pipermail с mail.python.org"""

    filter_cumulative: bool = True

    def get_url(self) -> str:
        return f'https://mail.python.org/pipermail/{self.alias}/'

    def __init__(self, *, previous_result: List, previous_dt: Optional[datetime], year_month: str = None, **kwargs):
        self.year_month = year_month
        super().__init__(previous_result=previous_result, previous_dt=previous_dt, **kwargs)

    def fetch(self) -> TypeFetcherResult:

        url = self.get_url()
        year_month = self.year_month

        details_page_file = '/date.html'

        if not year_month:
            page = get_from_url(url)

            match = re.search(r'="((\d{4}-[^/]+)%s)"' % details_page_file, page.text)

            if not match:
                sig_integration_failed.send(None, description=f'Subject page link not found at {url}')
                return

            year_month = match.group(2)

        page = get_from_url(f'{url}{year_month}{details_page_file}')
        soup = make_soup(page.text)

        items = {}

        prefix_re = re.compile(r'\[[^]]+\]\s*')

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

    site: str = None
    domain: str = None
    query_revision_id: int = None

    def __init__(self, *, previous_result: List, previous_dt: Optional[datetime], top_count: int = 10, **kwargs):
        self.top_count = top_count
        super().__init__(previous_result=previous_result, previous_dt=previous_dt, **kwargs)

    def get_url(self) -> str:
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

    def get_item_url(self, item_id: int) -> str:
        return f'https://{self.domain}/questions/{item_id}/'

    def fetch(self) -> TypeFetcherResult:
        url = self.get_url()
        response = get_from_url(url)

        items = {}

        reader = csv.DictReader(StringIO(response.text))

        for row in reader:
            item_id = row['id']
            item_url = self.get_item_url(item_id)
            item_title = row['Title']
            items[item_id] = SummaryItem(item_url, item_title)

        items, latest_result = self._filter(items)

        return items, latest_result
