from django.utils import timezone
from sitemessage.toolbox import check_undelivered, cleanup_sent_messages, send_scheduled_messages
from uwsgiconf.runtime.scheduling import register_cron, register_timer

from .commands import clean_missing_refs, publish_postponed
from .models import PEP, App, Event, ExternalResource, Summary, Vacancy
from .sitemessages import PythonzEmailDigest


def _nsk(hour: int) -> int:
    """Транслирует новосибирский час в час по времени страны хостинга.

    :param hour:

    """
    return hour - 6


@register_timer(60)
def task_send_messages(sig_num):
    """Отправка оповещений."""
    send_scheduled_messages(priority=1)


@register_cron(hour=-4, minute=30)
def task_get_vacancies(sig_num):
    """Синхронизация вакансий."""
    Vacancy.update_statuses()
    Vacancy.fetch_items()


@register_cron(hour=_nsk(15), minute=25)
def task_get_events(sig_num):
    """Синхронизация событий."""
    Event.fetch_items()


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
    if _nsk(13) <= timezone.now().hour < _nsk(21):
        publish_postponed()


@register_cron(weekday=0, hour=_nsk(14), minute=10)
def task_create_summary(sig_num):
    """Еженедельная статья-сводка.
    Воскресенье 14:10 Нск (10:10 Мск).

    """
    Summary.create_article()


@register_cron(weekday=5, hour=_nsk(13), minute=20)
def task_sync_peps(sig_num):
    """Синхронизация данных PEP.
    Пятница 13:20 Нск (9:20 Мск).

    """
    PEP.sync_from_repository()


@register_cron(weekday=5, hour=_nsk(7), minute=40)
def task_digest_create(sig_num):
    """Компиляция еженедельного дайджеста.
    Пятница 7:40 Нск (3:40 Мск).

    """
    PythonzEmailDigest.create()


@register_cron(weekday=5, hour=_nsk(13), minute=0)
def task_digest_send(sig_num):
    """Рассылка еженедельного дайджеста.
    Пятница 13:00 Нск (9:00 Мск).

    """
    send_scheduled_messages(priority=7)


@register_cron(weekday=0, hour=_nsk(7), minute=13)
def task_clean_missing_refs(sig_num):
    """Очистка от устаревших промахов справочника.
    Воскресенье 7:13 Нск (3:13 Мск).

    """
    clean_missing_refs()


@register_cron(weekday=0, hour=_nsk(7), minute=15)
def task_clean_sent_msg(sig_num):
    """Очистка от отправленных сообщений.
    Воскресенье 7:15 Нск (3:15 Мск).

    """
    cleanup_sent_messages()


@register_cron(hour=-14, minute=10)
def task_notify_undelivered(sig_num):
    """Оповещение о недоставленных сообщениях."""
    check_undelivered()


@register_cron(weekday=1, hour=_nsk(10), minute=5)
def task_app_stats_update(sig_num):
    """Обновление данных о загрузках приложений.
    Понедельник 10:05 Нск (6:05 Мск).

    """
    App.actualize_downloads()
