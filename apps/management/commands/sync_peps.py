from django.core.management.base import BaseCommand
from django.conf import settings

from ...models import PEP

#  PEP.sync_from_repository() может вызывать систему оповещений,
# для которой необходимо, чтобы работала reverse(). Подгружаем данные о доступных URL.
__import__(settings.ROOT_URLCONF)


class Command(BaseCommand):

    help = 'Updates local PEPs data using remote repository'

    def handle(self, *realm_names, **options):

        self.stdout.write('Starting PEP update ...\n')

        PEP.sync_from_repository()

        self.stdout.write('PEP update is done.\n')
