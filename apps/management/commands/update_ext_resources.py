from django.core.management.base import BaseCommand

from ...models import ExternalResource


class Command(BaseCommand):

    help = 'Updates remote resources.'

    def handle(self, *args, **options):

        self.stdout.write('Updating resources ...\n')
        ExternalResource.fetch_new()
        self.stdout.write('Resources updated.\n')
