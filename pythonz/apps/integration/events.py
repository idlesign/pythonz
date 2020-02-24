import re
from typing import List
from hashlib import md5

from icalendar_light.toolbox import Calendar

from .base import RemoteSource


class EventSource(RemoteSource):
    """База для источников событий."""

    realm: str = 'event'


class GoogleCalendarSource(EventSource):
    """Источник Google-календарь."""

    group: str = ''
    """Идентификатор группы гуглового календаря."""

    days_forward: int = 30
    """Количество дней, на которое требуется заглянуть вперёд в календаре."""

    big_events: bool = False
    """Указание на то, что все события группы масштабные."""

    @classmethod
    def construct_url(cls):
        return f'https://www.google.com/calendar/ical/{cls.group}@group.calendar.google.com/public/basic.ics'

    def compose_item(self, event: Calendar.Event) -> dict:

        try:
            url = re.findall(r'="([^"]+)"', event.description)[0]

        except IndexError:
            url = ''

        dt_start = event.dt_start

        item = {
            '__skip': False,
            'title': event.summary,
            'url': url,
            'src_id': md5(f'{event.uid}|{dt_start.date()}'.encode()).hexdigest(),
            'src_place_name': event.location,
            'time_start': dt_start,
            'time_finish': event.dt_end,
            'big': self.big_events,
        }

        return item

    def fetch_list(self) -> List[dict]:

        result = []

        compose = self.compose_item

        contents = self.request(self.construct_url())

        events = Calendar.iter_events_upcoming(contents.splitlines(), days_forward=self.days_forward)

        for event in events:
            if not event.status or event.status == 'CONFIRMED':
                result.append(compose(event))

        return result


class PyEvent(GoogleCalendarSource):
    """Официальный календарь крупных событий."""

    alias: str = 'pyglob'
    title: str = 'Официальный календарь'
    group: str = 'j7gov1cmnqr9tvg14k621j7t5c'

    big_events: bool = True


class PyUserGroupEvent(GoogleCalendarSource):
    """Календарь групп пользователей."""

    alias: str = 'pyuser'
    title: str = 'Календарь сообществ'
    group: str = '3haig2m9msslkpf2tn1h56nn9g'
