from django.core.management.base import BaseCommand

from ...models import Video, Book, Person
from ...utils import get_logger


LOG = get_logger(__name__)


class Command(BaseCommand):

    help = 'Links realms entities to person profiles.'

    def handle(self, *args, **options):

        LOG.info('Linking to persons ...')

        known_persons = Person.get_known_persons()

        for model_cls in (Video, Book):
            for item in model_cls.objects.all():  # type: Video
                item.sync_persons_fields(known_persons)

        LOG.info('Linking to persons done')
