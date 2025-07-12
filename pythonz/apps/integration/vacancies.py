
from django.utils.dateparse import parse_datetime

from .base import RemoteSource
from .utils import get_json


class VacancySource(RemoteSource):
    """База для источников вакансий."""

    realm: str = 'vacancy'

    @classmethod
    def get_status(cls, url: str) -> dict:
        raise NotImplementedError  # pragma: nocover


class HhVacancy(VacancySource):
    """Объединяет инструменты для работы с вакансиями с hh.ru."""

    alias: str = 'hh'
    title: str = 'hh.ru'

    @classmethod
    def get_status(cls, url: str) -> dict:
        """Возвращает состояние вакансии по указанному URL.

        :param url:

        """
        response = get_json(url, return_none_statuses={404}, silent_statuses={403})

        if not response:
            return response

        return response['archived']

    def fetch_list(self) -> list[dict]:
        """Возвращает словарь с данными вакансий, полученный из внешнего
        источника.

        """
        base_url = 'https://api.hh.ru/vacancies/'
        query = 'search_field=name&per_page=100&order_by=publication_time&period=1&text=python'
        response = get_json(f'{base_url}?{query}')

        if 'items' not in response:
            return []

        results = []

        for item in response['items']:

            if item['archived']:
                continue

            salary_from = salary_till = salary_currency = ''

            if item['salary']:
                salary = item['salary']
                salary_from = salary['from']
                salary_till = salary['to']
                salary_currency = salary['currency']

            employer = item['employer']
            url_logo = employer.get('logo_urls')

            if url_logo:
                url_logo = url_logo.get('90')

            results.append({
                'src_id': item['id'],
                'src_place_name': item['area']['name'],
                'src_place_id': item['area']['id'],
                'title': item['name'],
                'url': item['alternate_url'],
                'url_api': item['url'],
                'url_logo': url_logo,
                'employer_name': employer['name'],
                'salary_from': salary_from or None,
                'salary_till': salary_till or None,
                'salary_currency': salary_currency,
                'time_published': parse_datetime(item['published_at']),
            })

        return results
