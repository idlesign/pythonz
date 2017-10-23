from django.core.management.base import BaseCommand

from ...commands import publish_postponed


class Command(BaseCommand):

    help = 'Publishes posponed materials'

    def handle(self, *realm_names, **options):

        self.stdout.write('Postponed publishing started ...\n')

        publish_postponed()

        self.stdout.write('Postponed publishing finished.\n')
