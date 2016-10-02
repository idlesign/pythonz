from datetime import timedelta

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...realms import get_realms
from ...generics.models import RealmBaseModel


class Command(BaseCommand):

    help = 'Publishes posponed materials'

    def handle(self, *realm_names, **options):

        self.stdout.write('Postponed publishing started ...\n')

        status_postponed = RealmBaseModel.STATUS_POSTPONED
        status_published = RealmBaseModel.STATUS_PUBLISHED

        # В каждой области будем публиковать отложенные материалы,
        # если данный автор не публиковался более суток.
        date_before = timezone.now() - timedelta(days=1)

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
                latest = realm_model.objects.filter(
                    status=status_published, submitter_id=submitter_id,
                ).latest('time_published')

                if not latest or latest.time_published < date_before:
                    # Пока публикуем только первый из назначенных к публикации материалов.
                    # В последующем возможно логика будет усложнена.
                    item = items[0]
                    item.status = status_published
                    item.save()

        self.stdout.write('Postponed publishing finished.\n')
