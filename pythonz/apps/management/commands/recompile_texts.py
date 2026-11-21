from django.core.management.base import BaseCommand

from ...models import App, Article, Community, Discussion, Event, Person, Reference, Version


class Command(BaseCommand):

    help = 'Recompiles markdown texts into html.'

    def handle(self, *args, **options):

        self.stdout.write('Recompiling texts ...\n')

        models = [
            Discussion,
            Community,
            Article,
            Version,
            Reference,
            Event,
            Person,
            App,
        ]

        for model in models:

            for item in model.objects.all():
                item.mark_unmodified()
                item.save()

        self.stdout.write('Texts recompiled.\n')
