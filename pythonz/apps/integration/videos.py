from typing import Dict, Tuple

from ..exceptions import RemoteSourceError


class VideoBroker:

    EMBED_WIDTH: int = 560
    EMBED_HEIGHT: int = 315

    hostings: Dict[str, Tuple[str, ...]] = {
        'Vimeo': ('vimeo.com', 'vimeo'),
        'YouTube': ('youtu', 'youtube'),
    }
    hostings = dict(sorted(hostings.items(), key=lambda k: k[0]))

    @classmethod
    def get_data_from_vimeo(cls, url: str) -> Tuple[str, str]:

        from ..integration.utils import get_json

        if 'vimeo.com' not in url:  # http://vimeo.com/{id}
            raise RemoteSourceError(f'Не удалось обнаружить ID видео в URL `{url}`')

        video_id = url.rsplit('/', 1)[-1]

        embed_code = (
            f'<iframe src="//player.vimeo.com/video/{video_id}?byline=0&amp;portrait=0&amp;color=ffffff" '
            f'width="{cls.EMBED_WIDTH}" height="{cls.EMBED_HEIGHT}" frameborder="0" '
            'webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>')

        json = get_json(f'http://vimeo.com/api/v2/video/{video_id}.json')
        cover_url = json[0]['thumbnail_small']

        return embed_code, cover_url

    @classmethod
    def get_data_from_youtube(cls, url: str) -> Tuple[str, str]:

        if 'youtu.be' in url:  # http://youtu.be/{id}
            video_id = url.rsplit('/', 1)[-1]

        elif 'watch?v=' in url:  # http://www.youtube.com/watch?v={id}
            video_id = url.rsplit('v=', 1)[-1]

        else:
            raise RemoteSourceError(f'Не удалось обнаружить ID видео в URL `{url}`')

        cover_url = f"http://img.youtube.com/vi/{video_id.split('?', 1)[0]}/default.jpg"

        if '?' in video_id:
            video_id += '&'

        else:
            video_id += '?'

        video_id = video_id.replace('t=', 'start=') + 'rel=0'

        embed_code = (
            f'<iframe src="//www.youtube.com/embed/{video_id}" '
            f'width="{cls.EMBED_WIDTH}" height="{cls.EMBED_HEIGHT}" frameborder="0" allowfullscreen>'
            '</iframe>')

        return embed_code, cover_url

    @classmethod
    def get_hosting_for_url(cls, url: str) -> str:
        hosting = ''

        for title, data in cls.hostings.items():
            search_str, hid = data

            if search_str in url:
                hosting = hid
                break

        return hosting

    @classmethod
    def get_code_and_cover(cls, url: str, wrap_responsive: bool = False) -> Tuple[str, str]:

        url = url.rstrip('/')
        hid = cls.get_hosting_for_url(url)

        msg = f'Не удалось обнаружить обработчик для указанного URL `{url}`'

        if not hid:
            raise RemoteSourceError(msg)

        method_name = f'get_data_from_{hid}'
        method = getattr(cls, method_name, None)

        if method is None:
            raise RemoteSourceError(msg)

        embed_code, cover_url = method(url)

        if wrap_responsive:
            embed_code = f'<div class="embed-responsive embed-responsive-16by9">{embed_code}</div>'

        return embed_code, cover_url
