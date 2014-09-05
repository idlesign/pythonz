from sitecats.utils import get_category_model
from xross.toolbox import xross_view, xross_listener
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from .models import ModelWithCompiledText
from ..models import ModelWithOpinions, User, Opinion
from ..forms import OpinionForm
from ..exceptions import RedirectRequired


class RealmView(View):
    """Базовое представление для представлений областей (сущностей)."""

    realm = None  # Во время исполнения будет содержать ссылку на объект области Realm
    name = None  # Во время исполнения будет содержать алиас этого представления (н.п. edit).

    def get_template_path(self):
        """Возвращает путь к шаблону страницы.

        :return:
        """
        return 'realms/%s/%s.html' % (self.realm.name_plural, self.name)

    def render(self, request, data_dict):
        """Компилирует страницу представления.

        :param request:
        :param data_dict:
        :return:
        """
        data_dict.update({
            'realm': self.realm,
            'view_type': self.name
        })
        return render(request, self.get_template_path(), data_dict)

    def post(self, request, *args, **kwargs):
        """Запросы POST перенаправляются на обработчик GET.

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        return self.get(request, *args, **kwargs)

    def get_object_or_404(self, obj_id):
        """Реализует механизм обнаружения объекта нужного типа для области,
        к которой привязано это представление.

        :param obj_id:
        :return:
        """
        return get_object_or_404(self.realm.model, pk=obj_id)


class ListingView(RealmView):
    """Список объектов."""

    def get_paginator_objects(self):
        """Возвращает объект постраницчной навигации.

        :return:
        """
        return self.realm.model.get_paginator_objects()

    def get(self, request, category_id=None):
        page = request.GET.get('p')
        paginator = Paginator(self.get_paginator_objects(), self.realm.model.items_per_page)

        try:
            items = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            items = paginator.page(1)

        category = None
        if category_id is not None:
            category = get_category_model().objects.get(pk=category_id)

        return self.render(request, {self.realm.name_plural: items, 'category': category})


class DetailsView(RealmView):
    """Дательная информация об объекте."""

    def _handle_opinion_form(self, target_obj, request):
        """Реализует обработку данных формы со мнением.

        :param target_obj:
        :param request:
        :return:
        """
        opinion_form = OpinionForm(request.POST or None, user=request.user)

        if opinion_form.is_valid():
            opinion = opinion_form.save(commit=False)
            opinion.submitter = request.user
            opinion.linked_object = target_obj
            opinion.text = opinion.text_src
            opinion_form.save()
            raise RedirectRequired()

        return opinion_form

    def _attach_opinions_data(self, item, request):
        """Цепляет к объекту данные о привязанных к нему мнениях.

        :param item:
        :param request:
        :return:
        """
        if isinstance(item, ModelWithOpinions):
            opinions = item.opinions.order_by('-supporters_num', '-time_created').all()
            opinions_rates = item.get_suppport_for_objects(opinions, user=request.user)

            user_opinion = None
            for opinion in opinions:
                opinion.my_support = opinions_rates[opinion.id]
                if opinion.submitter_id == request.user.id:
                    user_opinion = opinion

            opinion_form = self._handle_opinion_form(item, request)

            item.opinions_data = {
                'all': opinions,
                'my': user_opinion,
                'form': opinion_form
            }

    def _attach_support_data(self, item, request):
        """Цепляет к объекту данные о поданном за него голосе пользователя.

        :param item:
        :param request:
        :return:
        """
        item.my_support = item.is_supported_by(request.user)

    def _attach_bookmark_data(self, item, request):
        """Цепляет к объекту данные о его занесении его пользователем в избранное.

        :param item:
        :param request:
        :return:
        """
        item.is_bookmarked = item.is_bookmarked_by(request.user)

    def _attach_data(self, item, request):
        """Цепляет базовый набор данный к объекту.

        :param item:
        :param request:
        :return:
        """
        self._attach_bookmark_data(item, request)
        self._attach_support_data(item, request)

    def rate_opinion(self, request, opinion_id, action, xross=None):
        """Используется xross. Реализует оценку мнения.

        :param request:
        :param opinion_id:
        :param action:
        :param xross:
        :return:
        """
        opinion = Opinion.objects.get(pk=opinion_id)
        if action == 1:
            opinion.my_support = True
            opinion.set_support(request.user)
        elif action == 0:
            opinion.my_support = False
            opinion.remove_support(request.user)
        return render(request, 'opinions/sub_rating.html', {'opinion': opinion})

    def list_opinions(self, request, xross=None):
        """Используется xross. Реализует получение списка мнений.

        :param request:
        :param xross:
        :return:
        """
        item = xross.attrs['item']
        self._attach_opinions_data(item, request)
        return render(request, 'opinions/sub_opinions.html', {'opinions': item.opinions_data})

    def toggle_bookmark(self, request, action, xross=None):
        """Используется xross. Реализует занесение/изъятие объекта в/из избранного..

        :param request:
        :param action:
        :param xross:
        :return:
        """
        item = xross.attrs['item']
        if action == 1:
            item.set_bookmark(self.request.user)
        elif action == 0:
            item.remove_bookmark(self.request.user)
        self._attach_bookmark_data(item, self.request)
        return render(self.request, 'sub_box_bookmark.html', {'item': item})

    def set_rate(self, request, action, xross=None):
        """Используется xross. Реализует оценку самого объекта.

        :param request:
        :param action:
        :param xross:
        :return:
        """
        item = xross.attrs['item']
        if action == 1:
            item.set_support(self.request.user)
        elif action == 0:
            item.remove_support(self.request.user)
        self._attach_support_data(item, self.request)
        return render(self.request, 'sub_box_rating.html', {'item': item})

    @xross_view(list_opinions, set_rate, toggle_bookmark, rate_opinion)
    def get(self, request, obj_id):

        item = self.get_object_or_404(obj_id)

        if isinstance(item, ModelWithOpinions):
            item.has_opinions = True

        xross_listener(item=item)

        try:
            self._handle_opinion_form(item, request)
            self._attach_data(item, request)
        except RedirectRequired:
            return redirect(item, permanent=True)

        try:
            item_edit_allowed = (request.user == item.submitter)
        except AttributeError:
            item_edit_allowed = (request.user == item)

        # Нарочно передаём item под двумя разными именами.
        # Требуется для упрощения наслования шаблонов.
        return self.render(request, {self.realm.name: item, 'item': item, 'item_edit_allowed': item_edit_allowed})


class TagsView(ListingView):
    """Список меток (категорий) для объекта."""

    def get_paginator_objects(self):
        return self.realm.model.get_categorized().order_by('title').all()


class EditView(RealmView):
    """Редактирование (и добавление) объекта."""

    @method_decorator(login_required)  # На страницах редактирования требуется атворизация.
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def preview_rst(self, request, text_src, xross=None):
        """Используется xross. Обрабатывает запрос на предварительный просмотр текста в формате rst.

        :param request:
        :param text_src:
        :param xross:
        :return:
        """
        if isinstance(xross.attrs['item'], ModelWithCompiledText):
            return HttpResponse(ModelWithCompiledText.compile_text(text_src))

    @xross_view(preview_rst)
    def get(self, request, obj_id=None):
        item = None

        if obj_id is not None:
            item = self.get_object_or_404(obj_id)

        xross_listener(item=item)

        form = self.realm.form(request.POST or None, request.FILES or None, instance=item, user=request.user)
        if item is None:
            form.submit_title = self.realm.model.txt_form_add
        else:

            if isinstance(item, User):
                # Редактировать пользователей могут только пользователи.
                if item != request.user:
                    raise PermissionDenied()
            else:
                # Редактирование объектов разрешено их создателям и суперпользвоателям.
                if item.submitter != request.user and not request.user.is_superuser:
                    raise PermissionDenied()

            form.submit_title = self.realm.model.txt_form_edit

        if form.is_valid():
            if item is None:
                item = form.save(commit=False)
                item.submitter = request.user
                item.save()
                form.save_m2m()
            else:
                form.save()
            return redirect(item, permanent=True)

        return self.render(request, {'form': form, self.realm.name: item})


class AddView(EditView):
    """Добавление объекта."""

    def get_template_path(self):
        return 'realms/%s/edit.html' % self.realm.name_plural
