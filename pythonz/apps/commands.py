from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from .generics.models import RealmBaseModel
from .models import ReferenceMissing
from .realms import get_realms


def publish_postponed():
    """Публикует материалы, назначенные к отложенной публикации."""
    status_postponed = RealmBaseModel.Status.POSTPONED
    status_published = RealmBaseModel.Status.PUBLISHED

    # В каждой области будем публиковать отложенные материалы,
    # если данный автор не публиковался более узананного периода.
    date_before = timezone.now() - timedelta(hours=22)

    for realm in get_realms().values():
        realm_model = realm.model
        postponed_by_submitter = defaultdict(list)

        qs = realm_model.objects.filter(status=status_postponed).order_by('time_created')

        for item in qs:
            submitter_id = getattr(item, 'submitter_id', None)

            if submitter_id is None:
                continue

            postponed_by_submitter[submitter_id].append(item)

        for submitter_id, items in postponed_by_submitter.items():

            try:
                latest = realm_model.objects.filter(
                    status=status_published,
                    submitter_id=submitter_id,
                    time_published__isnull=False,
                ).latest('time_published')

            except realm_model.DoesNotExist:
                latest = None

            if not latest or latest.time_published < date_before:
                # Пока публикуем только первый из назначенных к публикации материалов.
                # В последующем возможно логика будет усложнена.
                item = items[0]
                item.mark_published()
                item.save()


def clean_missing_refs(min_hits: int = 4):
    """Удаляет из БД записи о промахах справочника, получившиеся
    менее заданного количества обращений.

    :param min_hits:

    """
    ReferenceMissing.objects.filter(hits__lt=min_hits).delete()
