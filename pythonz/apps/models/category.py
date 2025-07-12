from django.db.models import Q, QuerySet
from django.urls import reverse
from sitecats.models import Category as Category_


class Category(Category_):
    """Посредник для мимикрии под области."""

    class Meta:

        proxy = True

    @classmethod
    def find(cls, *search_terms: str) -> QuerySet:
        """Ищет указанный текст в категориях. Возвращает QuerySet.

        :param search_terms: Строки для поиска.

        """
        q = Q()

        for term in search_terms:
            if term:
                q |= Q(title__icontains=term) | Q(note__icontains=term)

        return Category.objects.filter(q).order_by('time_created')

    @property
    def description(self) -> str:
        return self.note

    def get_absolute_url(self, **kwargs) -> str:
        # Сокращённая реализация из RealmBaseModel.
        return reverse(self.realm.get_details_urlname(), args=[self.id])
