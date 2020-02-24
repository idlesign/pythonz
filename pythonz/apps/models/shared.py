from ..utils import UTM


HINT_IMPERSONAL_REQUIRED = (
    '<strong>Без обозначения личного отношения. Личное отношение можно выразить в Обсуждениях к материалу.</strong>')


class UtmReady:
    """Примесь, добавляющая модели метод для получения URL с метками UTM."""

    url_attr: str = 'url'

    def get_utm_url(self) -> str:
        """Возвращает URL с UTM-метками."""
        return UTM.add_to_external_url(getattr(self, self.url_attr) or '')
