from siteprefs.toolbox import autodiscover_siteprefs
from sitegate.toolbox import get_sitegate_urls
from django.conf.urls import patterns, include, url
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

from apps.realms import bootstrap_realms  # Здесь относительный импорт работать не будет.
from apps.views import page_not_found, permission_denied, server_error

autodiscover_siteprefs()


urlpatterns = patterns('',
    url(r'^$', 'apps.views.index', name='index'),
    url(r'^login/$', 'apps.views.login', name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
    url(r'^promo/$', render, {'template_name': 'static/promo.html'}),
    url(r'^about/$', render, {'template_name': 'static/about.html'}),
    url(r'^sitemap/$', render, {'template_name': 'static/sitemap.html'}),
    url(r'^%s/' % settings.ADMIN_URL, include(admin.site.urls)),
)

urlpatterns += get_sitegate_urls()  # Цепляем URLы от sitegate,

bootstrap_realms(urlpatterns)  # Инициализируем области


# Используем собственные страницы ошибок.
handler403 = permission_denied
handler404 = page_not_found
handler500 = server_error


if settings.DEBUG:
    # Чтобы рабютала отладочная панель.
    import debug_toolbar
    urlpatterns += patterns('', url(r'^__debug__/', include(debug_toolbar.urls)),)
    # Чтобы статика раздавалась при runserver.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
