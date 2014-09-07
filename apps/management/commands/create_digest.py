from django.core.management.base import BaseCommand

from ...utils import create_digest as do_create


class Command(BaseCommand):

    help = 'Created dispatches for pythonz weekly digest.'

    def handle(self, *args, **options):


        self.stdout.write('Creating pythonz digest...\n')
        try:
            do_create()
        except Exception as e:
            self.stderr.write(self.style.ERROR('Digest creation failed: %s\n' % e))
        else:
            self.stdout.write('Digest is created.\n')
