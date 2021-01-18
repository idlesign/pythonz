from datetime import datetime

import pytest
from django.core.exceptions import FieldDoesNotExist

from pythonz.apps.realms import get_realm, PEP, Category, Article


@pytest.fixture
def check_page(request_client):

    def check(view, *, assertions, args=None, user=None):

        client = request_client(user=user)

        content = client.get(
            (view, args), follow=True
        ).content.decode()

        for assertion in assertions:
            assert assertion in content

        return content

    return check


@pytest.fixture
def check_realm(check_page, robot, monkeypatch, request_client):

    def check_realm_(alias, *, views_hooks: dict = None, obj_kwargs=None):

        views_hooks = views_hooks or {}
        obj_kwargs = obj_kwargs or {}

        realm = get_realm(alias)

        model = realm.model

        obj_title = f'{model._meta.verbose_name} заголовок'

        obj_kwargs_base = {
            'submitter': robot,
        }

        try:
            model._meta.get_field('title')
            obj_kwargs_base['title'] = obj_title

        except FieldDoesNotExist:
            pass

        if 'status' not in obj_kwargs:
            obj_kwargs_base['status'] = model.Status.PUBLISHED

        obj = model.objects.create(**{**obj_kwargs, **obj_kwargs_base})

        if 'listing' in realm.allowed_views:

            hook = views_hooks.get('listing')
            checks = []

            not hook and checks.extend([
                f'{model._meta.verbose_name_plural}<',
                f'{obj_title}',
            ])

            result = check_page(
                realm.get_listing_urlname(),
                assertions=checks)

            hook and hook(result)

        if 'details' in realm.allowed_views:

            hook = views_hooks.get('details')
            checks = []

            not hook and checks.extend([
                f'{obj_title}<',
            ])

            result = check_page(
                realm.get_details_urlname(),
                args={'obj_id': obj.id},
                assertions=checks)

            hook and hook(result)

        if 'edit' in realm.allowed_views:

            hook = views_hooks.get('edit')
            checks = []

            not hook and checks.extend([
                f'Выход</a>',
                f'{realm.txt_form_edit}</h1>',
            ])

            result = check_page(
                realm.get_edit_urlname(),
                args={'obj_id': obj.id},
                assertions=checks, user=robot)

            hook and hook(result)

        if realm.syndication_enabled:
            client = request_client(user=None)
            content = client.get(f'/{realm.name_plural}/feed/').content.decode()
            assert f'<guid isPermaLink="false">{realm.name}_{obj.id}</guid>' in content

    return check_realm_


def test_index(check_page):

    check_page('index', assertions=[
        'Вход</a>',
        'Статьи</a>',
        'Про Python</h1>',
    ])


def test_search_site(check_page):

    check_page('search_site', assertions=[
        'Поиск по сайту</h1>',
    ])


def test_search(check_page):

    check_page('search', assertions=[
        'Про Python</h1>',  # Перенаправление на главную.
    ])


def test_login(check_page):

    check_page('login', assertions=[
        'Регистрация</h2>',
    ])


def test_logout(check_page, robot):

    check_page('logout', assertions=[
        'Про Python</h1>',  # Перенаправление на главную.
    ], user=robot)


def test_settings(check_page, robot):

    check_page('settings', assertions=[
        'Выход</a>',
        'Настройки</h1>',
    ], user=robot)


def test_robots(check_page):

    check_page('robots_rule_list', assertions=[
        'User-agent',
    ])


def test_books(check_realm):
    check_realm('book')


def test_videos(check_realm):
    check_realm('video')


def test_events(check_realm):
    check_realm('event')


def test_vacancies(check_realm):
    check_realm('vacancy')


@pytest.mark.skip('Разобраться с resolve, использующим локаль')  # todo
def test_references(check_realm):
    check_realm('reference')


def test_articles(check_realm):
    check_realm('article')


def test_places(check_realm):
    check_realm('place')


def test_discussions(check_realm):
    check_realm('discussion')


def test_users(check_realm):
    check_realm(
        'user',
        obj_kwargs={'username': 'Пользователь заголовок'},
        views_hooks={'edit': lambda contents: True})


def test_communities(check_realm):
    check_realm('community')


def test_versions(check_realm):
    check_realm('version', obj_kwargs={
        'date': datetime.now()
    })


def test_peps(check_realm):
    check_realm('pep', obj_kwargs={
        'num': 1,
        'status': PEP.Status.ACTIVE,
    })


def test_persons(check_realm):
    check_realm('person', obj_kwargs={
        'name_en': 'Персона заголовок',
    })


def test_categories_feed(request_client, robot):
    client = request_client(user=None)

    category = Category(creator=robot, title='someti')
    category.save()

    article = Article(submitter=robot)
    article.mark_published()
    article.save()
    article.add_to_category(category, user=robot)

    content = client.get(f'/categories/{category.id}/feed/').content.decode()
    assert f'<guid isPermaLink="false">article_{article.id}</guid>' in content
