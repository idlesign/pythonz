from sys import argv

from django.conf.urls import include, url
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import logout
from siteprefs.toolbox import autodiscover_siteprefs
from sitegate.toolbox import get_sitegate_urls
from sitemessage.toolbox import get_sitemessage_urls
from robots.views import rules_list

from apps.realms import bootstrap_realms  # Здесь относительный импорт работать не будет.
from apps.views import page_not_found, permission_denied, server_error, index, search, login, telebot, user_settings


urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^search/site/$', render, {'template_name': 'static/search_site.html'}, name='search_site'),
    url(r'^search/$', search, name='search'),
    url(r'^login/$', login, name='login'),
    url(r'^settings/$', user_settings, name='settings'),
    url(r'^logout/$', logout, {'next_page': '/'}, name='logout'),
    url(r'^promo/$', render, {'template_name': 'static/promo.html'}),
    url(r'^about/$', render, {'template_name': 'static/about.html'}),
    url(r'^sitemap/$', render, {'template_name': 'static/sitemap.html'}),
    url(r'^robots\.txt', rules_list, name='robots_rule_list'),
    url(r'^%s/' % settings.TELEGRAM_BOT_URL, telebot),
    url(r'^%s/' % settings.ADMIN_URL, include(admin.site.urls)),
]

urlpatterns += get_sitegate_urls()  # Цепляем URLы от sitegate,
urlpatterns += get_sitemessage_urls()  # Цепляем URLы от sitemessage,

# Используем собственные страницы ошибок.
handler403 = permission_denied
handler404 = page_not_found
handler500 = server_error


if settings.DEBUG:
    # Чтобы рабютала отладочная панель.
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls)),]
    # Чтобы статика раздавалась при runserver.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


MIGRATION = len(argv) > 1 and argv[1] == 'migrate'
"""
Указание на то, что приложение вызвано из manage-скрипта с командой `migrate`.

"""

if not MIGRATION:
    # Начиная с Django 1.9 urls.py участвуют и в процессе
    # установки миграций. Исполнение кода, расположенного ниже
    # в ходе мигрирования не требуется.
    autodiscover_siteprefs()

    # Инициализируем области сайта.
    bootstrap_realms(urlpatterns)
