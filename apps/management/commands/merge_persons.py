from django.core.management.base import BaseCommand

from ...models import Person, PEP
from ...utils import get_logger


LOG = get_logger(__name__)


class Command(BaseCommand):

    help = 'Merges the first persons into second. Deletes the first.'
    args = '[stale_person_id target_person_id]'

    def add_arguments(self, parser):
        parser.add_argument('stale_person_id')
        parser.add_argument('target_person_id')

    def handle(self, stale_person_id, target_person_id, **options):

        LOG.info('Merging person %s into %s ...', stale_person_id, target_person_id)

        # Person exists sanity check
        Person.objects.get(pk=target_person_id)
        stale_person = Person.objects.get(pk=stale_person_id)

        # PEP authorship
        linker_model = PEP.authors.through
        linker_model.objects.filter(person_id=stale_person_id).update(person_id=target_person_id)

        stale_person.delete()

        LOG.info('Merging persons done')
