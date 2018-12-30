from django.core.management.base import BaseCommand

from ...models import Discussion, Community, Article, Version, Reference, Event, Person


class Command(BaseCommand):

    help = 'Recompiles rst-like texts into html.'

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
        ]

        for model in models:

            for item in model.objects.all():
                item.text_src = item.text_src.rstrip('-_')
                item.mark_unmodified()
                item.save()

        self.stdout.write('Texts recompiled.\n')
