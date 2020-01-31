import responses

from pythonz.apps.integration.utils import get_location_data


@responses.activate
def test_get_location_data():

    responses.add(
        responses.GET,
        'https://geocode-maps.yandex.ru/1.x/',
        json={'response': {
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
        }},
        status=200
    )

    result = get_location_data('Some')
    assert result == {
        'requested_name': 'Some',
        'type': 'xxx',
        'name': 'yyy',
        'country': 'zzz',
        'pos': 'b,a',
        'bounds': '1|2'
    }
