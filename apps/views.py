from sitegate.decorators import signin_view, signup_view, redirect_signedin
from sitegate.signup_flows.classic import SimpleClassicWithEmailSignup
from django.shortcuts import render

from .realms import get_realms


def index(request):
    return render(request, 'index.html', {'realms': get_realms()})


@redirect_signedin
@signin_view(widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label}, template='form_bootstrap3')
@signup_view(widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label}, template='form_bootstrap3', flow=SimpleClassicWithEmailSignup, verify_email=True)
def login(request):
    return render(request, 'static/login.html')
