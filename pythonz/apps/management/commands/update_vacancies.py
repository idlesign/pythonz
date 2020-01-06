from django.core.management.base import BaseCommand

from ...models import Vacancy


class Command(BaseCommand):

    help = 'Updates vacancies from remote sources.'

    def handle(self, *args, **options):

        self.stdout.write('Updating vacancies...\n')

        Vacancy.update_statuses()
        Vacancy.fetch_new()

        self.stdout.write('Vacancies updated.\n')
