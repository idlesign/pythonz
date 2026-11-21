import pytest
from django.urls import reverse

from pythonz.apps.generics.models import RealmBaseModel
from pythonz.apps.models import PEP, App, Article, Book, Category, Person, Place, Reference, ReferenceMissing, Version, Video
from pythonz.apps.search import find_exact, get_areas, search_areas

STATUS_PUBLISHED = RealmBaseModel.Status.PUBLISHED


@pytest.fixture
def url_search():
    return reverse('search')


@pytest.fixture
def url_suggest():
    return reverse('search_suggest')


@pytest.fixture
def person(robot):
    return Person.objects.create(
        name='Гвидо ван Россум',
        name_en='Guido van Rossum',
        status=STATUS_PUBLISHED,
        submitter=robot,
    )


@pytest.fixture
def category(robot):
    return Category.objects.create(creator=robot, title='Видео')


@pytest.fixture
def reference(robot):
    return Reference.objects.create(
        title='pip',
        type=Reference.Type.PACKAGE,
        status=STATUS_PUBLISHED,
        submitter=robot,
    )


def test_get_areas():

    by_model = {area.model: area for area in get_areas()}

    assert set(by_model) == {Category, Person, Reference, App, Article, Book, Video, Place, Version, PEP}
    assert by_model[Person].exact_fields == ('name', 'name_en')
    assert by_model[Category].exact_fields == ('title',)


def test_search_areas_groups_results(person, reference):

    results = search_areas('Гвидо')

    assert results.total == 1
    assert results.groups[0].area.model is Person
    assert results.groups[0].results == [person]


def test_search_areas_swapped_layout(person):
    # «guido», набранное в русской раскладке.
    results = search_areas('пгшвщ')

    assert results.total == 1
    assert results.groups[0].results == [person]


def test_search_areas_ranks_exact_title_first(robot, reference):

    Reference.objects.create(
        title='pip-tools', type=Reference.Type.PACKAGE,
        status=STATUS_PUBLISHED, submitter=robot)

    results = search_areas('pip')

    assert [obj.title for obj in results.groups[0].results] == ['pip', 'pip-tools']


def test_find_exact(person, category):

    assert find_exact('Guido van Rossum') == person
    assert find_exact('Гвидо ван Россум') == person
    assert find_exact('Видео') == category
    assert find_exact('ничего такого') is None


def test_search_view_empty_term(request_client, url_search):

    client = request_client()

    response = client.post(url_search, data={'text': ''})

    assert response.status_code == 302
    assert response['Location'] == reverse('index')


def test_search_view_exact_match_redirect(request_client, url_search, person):

    client = request_client()

    response = client.post(url_search, data={'text': 'Guido van Rossum'})

    assert response.status_code == 302
    assert response['Location'] == person.get_absolute_url()


def test_search_view_single_result_redirect(request_client, url_search, reference):

    client = request_client()

    response = client.post(url_search, data={'text': 'pip'})

    assert response.status_code == 302
    assert response['Location'] == reference.get_absolute_url()


def test_search_view_multiple_results(request_client, url_search, robot, reference):

    client = request_client()

    Reference.objects.create(
        title='pip-tools', type=Reference.Type.PACKAGE,
        status=STATUS_PUBLISHED, submitter=robot)

    response = client.post(url_search, data={'text': 'pip'})
    content = response.content.decode()

    assert 'Количество результатов: 2' in content
    assert 'Справочник' in content


def test_search_view_no_results(request_client, url_search):

    client = request_client()

    response = client.post(url_search, data={'text': 'абракадабра'})
    content = response.content.decode()

    assert 'ничего не найдено' in content
    assert ReferenceMissing.objects.filter(term='абракадабра').exists()


def test_suggest_view(request_client, url_suggest, person):

    client = request_client()

    response = client.get(url_suggest, {'q': 'г'})

    assert response.json() == {'results': []}

    response = client.get(url_suggest, {'q': 'Гвидо'})

    assert response.json() == {'results': [{
        'value': person.get_absolute_url(),
        'text': person.title,
        'area': 'Персоны',
    }]}
