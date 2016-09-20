from django.core.management.base import BaseCommand

from ...models import Reference


class Command(BaseCommand):

    help = 'Recompiles rst-like texts into html.'

    def handle(self, *args, **options):

        self.stdout.write('Recompiling texts ...\n')

        for item in Reference.objects.all():
            item.text_src = item.text_src.rstrip('-_')
            item.mark_unmodified()
            item.save()

        self.stdout.write('Texts recompiled.\n')
