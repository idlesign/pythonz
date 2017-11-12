from sitemessage.toolbox import send_scheduled_messages
from uwsgiconf.runtime.scheduling import register_timer, register_cron

from .commands import publish_postponed
from .models import Summary, PEP, ExternalResource, Vacancy
from .sitemessages import PythonzEmailDigest


@register_timer(60, signal_or_target='worker')
def task_send_messages(sig_num):
    """Отправка оповещений."""
    send_scheduled_messages(priority=1)


@register_cron(hour=-4, minute=30, signal_or_target='worker')
def task_get_vacancies(sig_num):
    """Синхронизация вакансий."""
    Vacancy.update_statuses()
    Vacancy.fetch_new()


@register_cron(hour=-2, minute=1, signal_or_target='worker')
def task_get_resources(sig_num):
    """Подтягивание данных из внешних ресурсов."""
    ExternalResource.fetch_new()


@register_cron(hour=-1, minute=10, signal_or_target='worker')
def task_publish_postponed(sig_num):
    """Публикация отложенных материалов."""
    publish_postponed()


@register_cron(weekday=0, hour=7, minute=10, signal_or_target='worker')
def task_create_summary(sig_num):
    """Еженедельная статья-сводка.
    Воскресенье 14:10 Нск.

    """
    Summary.create_article()


@register_cron(weekday=4, hour=1, minute=40, signal_or_target='worker')
def task_sync_peps(sig_num):
    """Синхронизация данных PEP.
    Четверг 06:40 Нск.

    """
    PEP.sync_from_repository()


@register_cron(weekday=5, hour=3, minute=40, signal_or_target='worker')
def task_digest_create(sig_num):
    """Компиляция еженедельного дайджеста.
    Пятница 08:40 Нск.

    """
    PythonzEmailDigest.create()


@register_cron(weekday=5, hour=4, minute=0, signal_or_target='worker')
def task_digest_send(sig_num):
    """Рассылка еженедельного дайджеста.
    Пятница 09:00 Нск.

    """
    send_scheduled_messages(priority=7)
