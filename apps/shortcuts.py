from django.contrib import messages


def message_info(request, message):
    """Регистрирует сообщение информирующего типа для вывода пользователю на странице.

    :param Request request:
    :param str message:
    :return:
    """
    messages.add_message(request, messages.INFO, message, extra_tags='info')


def message_warning(request, message):
    """Регистрирует предупреждающее сообщение для вывода пользователю на странице.

    :param Request request:
    :param str message:
    :return:
    """
    messages.add_message(request, messages.WARNING, message, extra_tags='warning')


def message_success(request, message):
    """Регистрирует ободряющее сообщение для вывода пользователю на странице.

    :param Request request:
    :param str message:
    :return:
    """
    messages.add_message(request, messages.SUCCESS, message, extra_tags='success')


def message_error(request, message):
    """Регистрирует сообщение об ошибке для вывода пользователю на странице.

    :param Request request:
    :param str message:
    :return:
    """
    messages.add_message(request, messages.ERROR, message, extra_tags='danger')
