from django.utils import timezone


class TimezoneMiddleware(object):
    """Устанавливает текущую временную зону."""

    def process_request(self, request):
        # Пока будем считать, что Нск - пуп Земли.
        # TODO При случае что-нибудь придумать. Возможно pysyge.
        timezone.activate('Asia/Novosibirsk')
