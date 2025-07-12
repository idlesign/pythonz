from collections import defaultdict

from .utils import get_json


def get_for_package(name: str) -> dict[str, int]:
    """Возвращает количество загрузок указанного пакета по месяцам
    по данным pypistats.org.

    https://pypistats.org/api/

    :param name:

    """
    data = get_json(f'https://pypistats.org/api/packages/{name}/overall?mirrors=true')

    if not data:
        return {}

    monthly = defaultdict(int)

    for item in data.get('data', []):
        month = item['date'].rsplit('-', 1)[0]
        monthly[month] += item['downloads']

    return monthly
