from django.core.management.base import BaseCommand

from ...models import Event


class Command(BaseCommand):

    help = 'Updates events from remote sources.'

    def handle(self, *args, **options):

        self.stdout.write('Updating events...\n')

        Event.fetch_items()

        self.stdout.write('Events updated.\n')
