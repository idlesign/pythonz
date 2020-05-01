from pythonz.apps.integration.videos import VideoBroker


def test_youtube():

    img_expected = 'http://img.youtube.com/vi/WW0DTSioHQU/default.jpg'

    emb, img = VideoBroker.get_data_from_youtube('https://youtu.be/WW0DTSioHQU')

    assert 'embed' in emb
    assert img == img_expected

    emb, img = VideoBroker.get_data_from_youtube('https://youtu.be/WW0DTSioHQU?some=1&other=2')
    assert 'embed' in emb
    assert img == img_expected
