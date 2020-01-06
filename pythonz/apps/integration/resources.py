import feedparser

from ..signals import sig_integration_failed


class PyDigestResource:
    """Инструменты для получения данных со внешнего ресурса pythondigest.ru."""

    mapping = None

    @classmethod
    def get_mapping(cls):
        """Возвращает словарь соотношений классов областей псевдонимам
        разделов.

        :return:
        """
        if cls.mapping is None:
            from ..realms import ArticleRealm, VideoRealm, EventRealm

            mapping = {
                ArticleRealm: ('article', 'authors'),
                VideoRealm: ('video',),
                EventRealm: ('event',),
            }
            cls.mapping = mapping

        return cls.mapping

    @classmethod
    def fetch_entries(cls):
        """Собирает данные (записи) со внешнего ресурса, соотнося их
        с разделами pythonz.

        :rtype: list
        """
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
                url = '%s%s/' % (base_url, alias)

                try:
                    parsed = feedparser.parse(url)

                except Exception as e:
                    sig_integration_failed.send(None, description='URL %s. Error: %s' % (url, e))

                else:
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
