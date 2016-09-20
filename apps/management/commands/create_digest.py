from django.core.management.base import BaseCommand

from ...sitemessages import PythonzEmailDigest


class Command(BaseCommand):

    help = 'Created dispatches for pythonz weekly digest.'

    def handle(self, *args, **options):

        self.stdout.write('Creating pythonz digest...\n')
        PythonzEmailDigest.create()
        self.stdout.write('Digest is created.\n')
