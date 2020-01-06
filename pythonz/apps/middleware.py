from pytz import UnknownTimeZoneError
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser


def TimezoneMiddleware(get_response):
    """Устанавливает текущую временную зону."""

    def middleware(request):

        default_timezone = 'Asia/Novosibirsk'
        current_timezone = default_timezone

        user = getattr(request, 'user', None)
        if user is not None and not isinstance(user, AnonymousUser):
            if user.timezone:
                current_timezone = user.timezone

        try:
            timezone.activate(current_timezone)
        except UnknownTimeZoneError:
            timezone.activate(default_timezone)

        response = get_response(request)

        return response

    return middleware
