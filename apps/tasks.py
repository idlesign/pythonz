from datetime import datetime

from sitemessage.toolbox import send_scheduled_messages
from uwsgiconf.runtime.scheduling import register_timer, register_cron

from .commands import publish_postponed
from .models import Summary, PEP, ExternalResource, Vacancy
from .sitemessages import PythonzEmailDigest


@register_timer(60)
def task_send_messages(sig_num):
    """Отправка оповещений."""
    send_scheduled_messages(priority=1)


@register_cron(hour=-4, minute=30)
def task_get_vacancies(sig_num):
    """Синхронизация вакансий."""
    Vacancy.update_statuses()
    Vacancy.fetch_new()


@register_cron(hour=-2, minute=1)
def task_get_resources(sig_num):
    """Подтягивание данных из внешних ресурсов."""
    ExternalResource.fetch_new()


@register_cron(hour=-2, minute=15)
def task_publish_postponed(sig_num):
    """Публикация отложенных материалов.

    Не ранее 13 Нск (9 Мск).
    Не позднее 21 Нск (17 Мск).

    """
    if 6 <= datetime.utcnow().hour < 14:
        publish_postponed()


@register_cron(weekday=0, hour=8, minute=10)
def task_create_summary(sig_num):
    """Еженедельная статья-сводка.
    Воскресенье 14:10 Нск (10:10 Мск).

    """
    Summary.create_article()


@register_cron(weekday=5, hour=7, minute=20)
def task_sync_peps(sig_num):
    """Синхронизация данных PEP.
    Пятница 13:20 Нск (9:20 Мск).

    """
    PEP.sync_from_repository()


@register_cron(weekday=5, hour=1, minute=40)
def task_digest_create(sig_num):
    """Компиляция еженедельного дайджеста.
    Пятница 7:40 Нск (3:40 Мск).

    """
    PythonzEmailDigest.create()


@register_cron(weekday=5, hour=7, minute=0)
def task_digest_send(sig_num):
    """Рассылка еженедельного дайджеста.
    Пятница 13:00 Нск (9:00 Мск).

    """
    send_scheduled_messages(priority=7)
