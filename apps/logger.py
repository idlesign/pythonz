import logging


def get_logger(name):
    """Возвращает объект-журналёр для использования в модулях.

    :param name:
    :rtype: logging.Logger
    """
    return logging.getLogger('pythonz.%s' % name)
