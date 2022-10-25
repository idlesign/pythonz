import json

import pytest

from pythonz.apps.integration.utils import get_location_data, get_page_info


@pytest.mark.slow
def test_get_page_info():
    info = get_page_info('https://pythonz.net/videos/127/')
    assert info is None


def test_get_location_data(response_mock):

    json_response = json.dumps({'response': {
        'GeoObjectCollection': {
            'metaDataProperty': {'GeocoderResponseMetaData': {'found': 1}},
            'featureMember': [
                {'GeoObject': {
                    'Point': {'pos': 'a b'},
                    'boundedBy': {'Envelope': {'lowerCorner': '1', 'upperCorner': '2'}},
                    'metaDataProperty': {
                        'GeocoderMetaData': {
                            'kind': 'xxx',
                            'text': 'yyy',
                            'AddressDetails': {'Country': {'CountryName': 'zzz'}}
                        }
                    }
                }}
            ]
        }
    }})

    with response_mock(f'GET https://geocode-maps.yandex.ru/1.x/ -> 200 :{json_response}'):
        result = get_location_data('Some')

    assert result == {
        'requested_name': 'Some',
        'type': 'xxx',
        'name': 'yyy',
        'country': 'zzz',
        'pos': 'b,a',
        'bounds': '1|2'
    }
