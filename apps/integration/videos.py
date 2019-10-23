from collections import OrderedDict

from ..exceptions import RemoteSourceError


class VideoBroker:

    EMBED_WIDTH = 560
    EMBED_HEIGHT = 315

    hostings = OrderedDict(sorted({

        'Vimeo': ('vimeo.com', 'vimeo'),
        'YouTube': ('youtu', 'youtube'),

    }.items(), key=lambda k: k[0]))

    @classmethod
    def get_data_from_vimeo(cls, url):
        from ..integration.utils import get_json

        if 'vimeo.com' not in url:  # http://vimeo.com/{id}
            raise RemoteSourceError('Не удалось обнаружить ID видео в URL `%s`' % url)

        video_id = url.rsplit('/', 1)[-1]

        embed_code = (
            '<iframe src="//player.vimeo.com/video/%s?byline=0&amp;portrait=0&amp;color=ffffff" '
            'width="%s" height="%s" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen>'
            '</iframe>' % (video_id, cls.EMBED_WIDTH, cls.EMBED_HEIGHT))

        json = get_json('http://vimeo.com/api/v2/video/%s.json' % video_id)
        cover_url = json[0]['thumbnail_small']

        return embed_code, cover_url

    @classmethod
    def get_data_from_youtube(cls, url):

        if 'youtu.be' in url:  # http://youtu.be/{id}
            video_id = url.rsplit('/', 1)[-1]

        elif 'watch?v=' in url:  # http://www.youtube.com/watch?v={id}
            video_id = url.rsplit('v=', 1)[-1]

        else:
            raise RemoteSourceError('Не удалось обнаружить ID видео в URL `%s`' % url)

        embed_code = (
            '<iframe src="//www.youtube.com/embed/%s?rel=0" '
            'width="%s" height="%s" frameborder="0" allowfullscreen>'
            '</iframe>' % (video_id, cls.EMBED_WIDTH, cls.EMBED_HEIGHT))

        cover_url = 'http://img.youtube.com/vi/%s/default.jpg' % video_id

        return embed_code, cover_url

    @classmethod
    def get_hosting_for_url(cls, url):
        hosting = None

        for title, data in cls.hostings.items():
            search_str, hid = data

            if search_str in url:
                hosting = hid
                break

        return hosting

    @classmethod
    def get_code_and_cover(cls, url, wrap_responsive=False):

        url = url.rstrip('/')
        hid = cls.get_hosting_for_url(url)

        msg = 'Не удалось обнаружить обработчик для указанного URL `%s`' % url

        if hid is None:
            raise RemoteSourceError(msg)

        method_name = 'get_data_from_%s' % hid
        method = getattr(cls, method_name, None)

        if method is None:
            raise RemoteSourceError(msg)

        embed_code, cover_url = method(url)

        if wrap_responsive:
            embed_code = '<div class="embed-responsive embed-responsive-16by9">%s</div>' % embed_code

        return embed_code, cover_url
