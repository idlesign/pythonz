from datetime import datetime

import pytest
from django.core.exceptions import FieldDoesNotExist
from sitecats.models import ModelWithCategory

from pythonz.apps.realms import get_realm, PEP, Category, Article


@pytest.fixture
def check_page(request_client):

    def check(view, *, assertions, args=None, user=None, data: dict = None):

        client = request_client(user=user)

        kwargs = {}
        if data is None:
            method = client.get
        else:
            method = client.post
            kwargs['data'] = data

        content = method(
            (view, args),
            **kwargs,
            follow=True
        ).content.decode()

        for assertion in assertions:
            assert assertion in content

        return content

    return check


@pytest.fixture
def init_category(robot, monkeypatch):

    def init_category_(*, title):
        category, _ = Category.objects.get_or_create(
            creator=robot,
            title=title,
        )
        return category

    return init_category_


@pytest.fixture
def check_realm(check_page, robot, monkeypatch, request_client, init_category):

    def check_realm_(alias, *, views_hooks: dict = None, obj_kwargs=None, add_kwargs=None):

        views_hooks = views_hooks or {}
        obj_kwargs = obj_kwargs or {}
        add_kwargs = add_kwargs or {}

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

        supports_categories = issubclass(model, ModelWithCategory)

        if supports_categories:
            category_1 = init_category(title='catone')
            obj.add_to_category(category_1, user=robot)

        if 'listing' in realm.allowed_views:

            hook = views_hooks.get('listing')
            checks = []

            if supports_categories:
                checks.append(f'small">{category_1.title}</a>')

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

        if 'add' in realm.allowed_views and add_kwargs:

            add_kwargs.update({
                'pythonz_form': '1',
                '__submit': 'siteform',
            })

            hook = views_hooks.get('add')
            checks = []

            not hook and checks.extend([
                'title="Добавил: ',  # страница деталей содержит этот текст

            ])

            result = check_page(
                realm.get_add_urlname(),
                data=add_kwargs,
                args={},
                assertions=checks, user=robot)

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
        'Вход</h2>',
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


def test_events(check_realm, request_client):

    check_realm('event', add_kwargs={
        'title': 'one',
        'type': '1',
        'specialization': '1',
        'description': '3123',
        'text_src': 'qwreewr',
    })


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
        obj_kwargs={'username': 'Пользователь заголовок', 'profile_public': True},
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


def test_categories_feed(request_client, robot, init_category):
    client = request_client(user=None)

    category = init_category(title='someti')

    article = Article(submitter=robot)
    article.mark_published()
    article.save()
    article.add_to_category(category, user=robot)

    content = client.get(f'/categories/{category.id}/feed/').content.decode()
    assert f'<guid isPermaLink="false">article_{article.id}</guid>' in content
