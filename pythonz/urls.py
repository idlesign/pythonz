from sys import argv

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import (
    LogoutView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView, PasswordResetCompleteView
)
from django.shortcuts import render
from django.urls import path, include
from robots.views import rules_list
from sitegate.toolbox import get_sitegate_urls
from sitemessage.toolbox import get_sitemessage_urls

from .apps.realms import bootstrap_realms
from .apps.views import page_not_found, permission_denied, server_error, index, search, login, telebot, user_settings
from .apps.views.search import get_results

urls_password_reset = [
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

urlpatterns = [
    path('', index, name='index'),
    path('search/site/', render, {'template_name': 'static/search_site.html'}, name='search_site'),
    path('search/', search, name='search'),
    path('get_results/', get_results, name='get_results'),
    path('auth/', include(urls_password_reset)),
    path('login/', login, name='login'),
    path('settings/', user_settings, name='settings'),
    path('logout/', LogoutView.as_view(), {'next_page': '/'}, name='logout'),
    path('promo/', render, {'template_name': 'static/promo.html'}),
    path('about/', render, {'template_name': 'static/about.html'}),
    path('sitemap/', render, {'template_name': 'static/sitemap.html'}),
    path('robots.txt', rules_list, name='robots_rule_list'),
    path(f'{settings.TELEGRAM_BOT_URL}/', telebot),
    path(f'{settings.ADMIN_URL}/', admin.site.urls),
]

urlpatterns += get_sitegate_urls()  # Цепляем URLы от sitegate,
urlpatterns += get_sitemessage_urls()  # Цепляем URLы от sitemessage,

# Используем собственные страницы ошибок.
handler403 = permission_denied
handler404 = page_not_found
handler500 = server_error


if settings.DEBUG:
    # Чтобы работала отладочная панель.
    import debug_toolbar
    from django.conf.urls import include, url

    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls)),]
    # Чтобы статика раздавалась при runserver.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


MIGRATION = len(argv) > 1 and argv[1] == 'migrate'
"""
Указание на то, что приложение вызвано из manage-скрипта с командой `migrate`.

"""

if not MIGRATION:
    # Инициализируем области сайта.
    bootstrap_realms(urlpatterns)
