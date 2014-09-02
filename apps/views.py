from sitegate.decorators import signin_view, signup_view, redirect_signedin
from sitegate.signup_flows.classic import SimpleClassicWithEmailSignup
from django.shortcuts import render

from .realms import get_realms


def index(request):

    # from sitemessage.toolbox import send_scheduled_messages, schedule_messages, recipients
    # from sitemessage.utils import get_registered_messenger_object, get_registered_messenger_objects

    # msgr = get_registered_messenger_object('xmppsleek')
    # msgr.send_test_message('idlesign@ya.ru', 'bboooo')

    # msgr = get_registered_messenger_object('smtp')
    # msgr.send_test_message('idlesign@yandex.ru', 'HПроверка отсылки сообщей. Может на этот раз не будет считаться спамом %)')

    # msgr = get_registered_messenger_object('twitter')
    # msgr.send_test_message('idlesign', 'Ещё привет от django-sitemessage')


    # from sitemessage.messengers import SMTPMessenger, XMPPSleekMessenger
    #
    # from sitemessage.schortcuts import schedule_email
    # from django.contrib.auth.models import User

    # umodel = User(username='aaa', email='idlesign@yandex.ru')

    # schedule_messages('Проверка массовой рассылки xmpp %)', recipients('sleekxmpp', ['idlesign@ya.ru', 'broskaya@ya.ru']))
    # schedule_messages('Проверка массовой рассылки smtp %)', recipients('smtp', ['idlesign@yandex.ru', 'idlesing@yandex.ru']), request.user)
    # schedule_email('That\'s the message we send.', [umodel, 'idlesing@yandex.ru'], 'Message subject', request.user)
    #
    # from sitemessage.messages import EmailHtmlMessage
    # schedule_messages(
    #     [
    #         EmailHtmlMessage('Проба пера html', '<html><head></head><body>AAA <b>BBBB</b> %)<br/> Вот такие дела!</body></html>'),
    #         EmailHtmlMessage('Проба пера template', {'title': 'asddd', 'item': 'AAA <b>BBBB</b> %)<br/> Вот такие дела!'}),
    #     ],
    #     recipients('smtp', ['idlesign@yandex.ru', 'idlesing@yandex.ru']),
    #     request.user
    # )

    # send_scheduled_messages()

    # from .utils import get_location_data
    # print(get_location_data('Россия'))
    # print(get_location_data('Новосибирск'))
    # print(get_location_data('Новосибирск Грибоедова 34'))
    return render(request, 'index.html', {'realms': get_realms()})


@redirect_signedin
@signin_view(widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label}, template='form_bootstrap3')
@signup_view(widget_attrs={'class': 'form-control', 'placeholder': lambda f: f.label}, template='form_bootstrap3', flow=SimpleClassicWithEmailSignup, verify_email=True)
def login(request):
    return render(request, 'static/login.html')
