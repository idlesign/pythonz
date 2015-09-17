from traceback import print_exc

from django.core.management.base import BaseCommand

from ...models import ExternalResource


class Command(BaseCommand):

    help = 'Updates remote resources.'

    def handle(self, *args, **options):

        self.stdout.write('Updating resources ...\n')
        try:
            ExternalResource.fetch_new()

        except Exception as e:
            self.stderr.write(self.style.ERROR('Resources fetching failed: %s\n' % e))
            print_exc()
        else:
            self.stdout.write('Resources updated.\n')
