from django.utils.dateparse import parse_datetime

from .utils import get_json


class HhVacancyManager:
    """Объединяет инструменты для работы с вакансиями с hh.ru."""

    @classmethod
    def get_status(cls, url):
        """Возвращает состояние вакансии по указанному URL.

        :param url:
        :return:
        """
        response = get_json(url, return_none_statuses=[404])
        if not response:
            return response

        return response['archived']

    @classmethod
    def fetch_list(cls):
        """Возвращает словарь с данными вакансий, полученный из внешнего
        источника.

        :return:
        """
        base_url = 'https://api.hh.ru/vacancies/'
        query = (
            'search_field=%(field)s&per_page=%(per_page)s'
            '&order_by=publication_time&period=1&text=%(term)s' % {
                'term': 'python',
                'per_page': 100,
                'field': 'name',  # description
        })

        response = get_json('%s?%s' % (base_url, query))

        if 'items' not in response:
            return None

        results = []
        for item in response['items']:
            salary_from = salary_till = salary_currency = ''

            if item['salary']:
                salary = item['salary']
                salary_from = salary['from']
                salary_till = salary['to']
                salary_currency = salary['currency']

            employer = item['employer']
            url_logo = employer['logo_urls']
            if url_logo:
                url_logo = url_logo.get('90')

            results.append({
                '__archived': item['archived'],
                'src_id': item['id'],
                'src_place_name': item['area']['name'],
                'src_place_id': item['area']['id'],
                'title': item['name'],
                'url_site': item['alternate_url'],
                'url_api': item['url'],
                'url_logo': url_logo,
                'employer_name': employer['name'],
                'salary_from': salary_from or None,
                'salary_till': salary_till or None,
                'salary_currency': salary_currency,
                'time_published': parse_datetime(item['published_at']),
            })

        return results