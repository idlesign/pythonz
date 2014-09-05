from siteprefs.toolbox import autodiscover_siteprefs
from sitegate.toolbox import get_sitegate_urls
from django.conf.urls import patterns, include, url
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

from apps.realms import get_realms_urls, build_sitetree  # Здесь относительный импорт работать не будет.

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
urlpatterns += get_realms_urls()  # Цепляем URLы областей сайта.

build_sitetree()  # Строим древо сайта налету.


if settings.DEBUG:
    # Чтобы рабютала отладочная панель.
    import debug_toolbar
    urlpatterns += patterns('', url(r'^__debug__/', include(debug_toolbar.urls)),)
    # Чтобы статика раздавалась при runserver.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
