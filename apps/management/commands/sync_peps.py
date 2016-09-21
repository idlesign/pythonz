from django.core.management.base import BaseCommand

from ...models import PEP


class Command(BaseCommand):

    help = 'Updates local PEPs data using remote repository'

    def handle(self, *realm_names, **options):

        self.stdout.write('Starting PEP update ...\n')

        PEP.sync_from_repository()

        self.stdout.write('PEP update is done.\n')
