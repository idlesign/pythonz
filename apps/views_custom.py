from sitecats.toolbox import get_category_model, get_category_lists, get_category_aliases_under
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.defaults import page_not_found as dj_page_not_found, \
    permission_denied as dj_permission_denied, \
    server_error as dj_server_error

from .generics.views import DetailsView, RealmView


class UserDetailsView(DetailsView):
    """Перекрываем представление с детальной информацией для пользователей,
    чтобы поместить в контекст шаблона дополнительную информацию."""

    def _update_context(self, context):
        user = context['item']
        context['bookmarks'] = user.get_bookmarks()  # TODO проверить наполнение, возможно убрать области без закладок


class CategoryListingView(RealmView):
    """Выводит список известных категорий, либо список сущностей для конкретной категории."""

    def get(self, request, obj_id=None):
        from apps.realms import get_realms
        if obj_id is None:  # Запрошен список всех известных категорий.
            item = get_category_lists(
                init_kwargs={
                    'show_title': True,
                    'show_links': lambda cat: reverse(self.realm.get_details_urlname(), args=[cat.id])
                },
                additional_parents_aliases=get_category_aliases_under())
            return self.render(request, {'item': item})

        # Выводим список материалов (разбитых по областям сайта) для конкретной категории.
        category_model = get_category_model()
        category = get_object_or_404(category_model.objects.select_related('parent'), pk=obj_id)

        realm_list = []
        for realm in get_realms():
            if hasattr(realm.model, 'categories'):  # ModelWithCategory
                objs = realm.model.get_objects_in_category(category)[:5]
                if objs:
                    realm_list.append({
                        'objects': objs,
                        'url': reverse(realm.get_tags_urlname(), args=[category.id]),
                        'realm': realm
                    })

        return self.render(request, {self.realm.name: category, 'item': category, 'realm_list': realm_list})


# Наши страницы ошибок.
permission_denied = lambda request: dj_permission_denied(request, template_name='static/403.html')
page_not_found = lambda request: dj_page_not_found(request, template_name='static/404.html')
server_error = lambda request: dj_server_error(request, template_name='static/500.html')
