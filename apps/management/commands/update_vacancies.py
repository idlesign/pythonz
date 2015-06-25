from traceback import print_exc

from django.core.management.base import BaseCommand

from ...models import Vacancy


class Command(BaseCommand):

    help = 'Updates vacancies from remote sources.'

    def handle(self, *args, **options):

        self.stdout.write('Updating vacancies...\n')
        try:
            Vacancy.update_statuses()
            Vacancy.fetch_new()
        except Exception as e:
            self.stderr.write(self.style.ERROR('Vacancies fetching failed: %s\n' % e))
            print_exc()
        else:
            self.stdout.write('Vacancies updated.\n')
