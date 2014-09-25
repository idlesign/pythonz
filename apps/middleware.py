from django.utils import timezone
from pytz import UnknownTimeZoneError


class TimezoneMiddleware(object):
    """Устанавливает текущую временную зону."""

    def process_request(self, request):
        default_timezone = 'Asia/Novosibirsk'
        current_timezone = default_timezone

        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            if user.timezone:
                current_timezone = user.timezone

        try:
            timezone.activate(current_timezone)
        except UnknownTimeZoneError:
            timezone.activate(default_timezone)
