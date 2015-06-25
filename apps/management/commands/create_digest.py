from traceback import print_exc

from django.core.management.base import BaseCommand

from ...sitemessages import PythonzEmailDigest


class Command(BaseCommand):

    help = 'Created dispatches for pythonz weekly digest.'

    def handle(self, *args, **options):

        self.stdout.write('Creating pythonz digest...\n')
        try:
            PythonzEmailDigest.create()
        except Exception as e:
            self.stderr.write(self.style.ERROR('Digest creation failed: %s\n' % e))
            print_exc()
        else:
            self.stdout.write('Digest is created.\n')
