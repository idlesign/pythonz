from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from pytz import UnknownTimeZoneError


def TimezoneMiddleware(get_response):
    """Устанавливает текущую временную зону."""

    def middleware(request: HttpRequest) -> HttpResponse:

        default_timezone = 'Asia/Novosibirsk'
        current_timezone = default_timezone

        user = getattr(request, 'user', None)

        if user is not None and not isinstance(user, AnonymousUser):
            if tz := user.timezone:
                current_timezone = tz

        try:
            timezone.activate(current_timezone)

        except UnknownTimeZoneError:
            timezone.activate(default_timezone)

        response = get_response(request)

        return response

    return middleware
