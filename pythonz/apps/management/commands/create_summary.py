from django.core.management.base import BaseCommand

from ...models import Summary


class Command(BaseCommand):

    help = 'Creates summary article using data from external sources.'

    def handle(self, *args, **options):

        self.stdout.write('Creating summary ...\n')
        Summary.create_article()
        self.stdout.write('Summary is created.\n')
