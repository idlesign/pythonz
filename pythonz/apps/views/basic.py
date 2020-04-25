from django.http import HttpResponse
from django.shortcuts import render
from django.views.defaults import (
    page_not_found as dj_page_not_found,
    permission_denied as dj_permission_denied,
    server_error as dj_server_error
)
from sitegate.decorators import signin_view, signup_view, redirect_signedin
from sitegate.signup_flows.classic import SimpleClassicWithEmailSignup

from ..generics.views import HttpRequest


# Наши страницы ошибок.
def permission_denied(request: HttpRequest, exception: Exception) -> HttpResponse:
    return dj_permission_denied(request, exception, template_name='static/403.html')


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    return dj_page_not_found(request, exception, template_name='static/404.html')


def server_error(request: HttpRequest):
    return dj_server_error(request, template_name='static/500.html')


@redirect_signedin
@signin_view(
    widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label},
    template='form_bootstrap4'
)
@signup_view(
    widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label},
    template='form_bootstrap4',
    flow=SimpleClassicWithEmailSignup,
    verify_email=True
)
def login(request: HttpRequest) -> HttpResponse:
    """Страница авторизации и регистрации."""
    return render(request, 'static/login.html')
