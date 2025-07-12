
import feedparser

from ..signals import sig_integration_failed
from ..utils import get_logger

if False:  # pragma: nocover
    from ..generics.realms import RealmBase  # noqa

LOG = get_logger(__name__)


class PyDigestResource:
    """Инструменты для получения данных со внешнего ресурса pythondigest.ru."""

    mapping: dict[type['RealmBase'], tuple[str, ...]] = None

    @classmethod
    def get_mapping(cls) -> dict[type['RealmBase'], tuple[str, ...]]:
        """Возвращает словарь соотношений классов областей псевдонимам разделов."""

        if cls.mapping is None:
            from ..realms import ArticleRealm, VideoRealm  # noqa: PLC0415

            mapping = {
                ArticleRealm: ('article',),
                VideoRealm: ('video',),
            }
            cls.mapping = mapping

        return cls.mapping

    @classmethod
    def fetch_entries(cls) -> list[dict]:
        """Собирает данные (записи) со внешнего ресурса, соотнося их с разделами pythonz."""

        base_url = 'http://pythondigest.ru/rss/'

        mapping = cls.get_mapping()
        if not mapping:
            return []

        results = []
        known_links = []

        for realm, aliases in mapping.items():
            realm_name, _ = realm.get_names()

            entries_max = 5
            if len(aliases) > 1:
                entries_max = 3

            for alias in aliases:
                url = f'{base_url}{alias}/'

                try:
                    parsed = feedparser.parse(url)

                except Exception as e:
                    LOG.exception('Fetch digest error')
                    sig_integration_failed.send(None, description=f'URL {url}. Error: {e}')

                else:

                    # reverse - по степени свежести (более свежие в конце).
                    for entry in reversed(parsed.entries[:entries_max]):
                        link = entry.link
                        if link in known_links:
                            continue

                        known_links.append(link)
                        results.append({
                            'realm_name': realm_name,
                            'url': link,
                            'title': entry.title,
                            'description': entry.summary,
                        })

        return results
