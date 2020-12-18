import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


def init_sentry(*,dsn: str):
    """Инициализирует машинерию Сентри.

    :param dsn: Адрес для отправки событий.

    """
    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.3,
        send_default_pii=True,
        max_breadcrumbs=10,
    )
