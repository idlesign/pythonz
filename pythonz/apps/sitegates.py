from django.conf import settings
from sitegate.signin_flows.remotes.google import Google
from sitegate.signin_flows.remotes.yandex import Yandex
from sitegate.utils import register_remotes

register_remotes(
    Yandex(client_id=settings.SITEGATE_REMOTES['yandex']),
    Google(client_id=settings.SITEGATE_REMOTES['google']),
)
