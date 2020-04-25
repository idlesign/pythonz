from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from ..generics.views import HttpRequest
from ..integration.telegram import handle_request


@csrf_exempt
def telebot(request: HttpRequest) -> HttpResponse:
    """Обрабатывает запросы от Telegram.

    :param request:

    """
    handle_request(request)
    return HttpResponse()
