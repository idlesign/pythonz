from traceback import print_exc

from django.core.management.base import BaseCommand

from ...models import Reference


class Command(BaseCommand):

    help = 'Recompiles rst-like texts into html.'

    def handle(self, *args, **options):

        self.stdout.write('Recompiling texts ...\n')

        try:
            for item in Reference.objects.all():
                item.text_src.rstrip('-_')
                item.mark_unmodified()
                item.save()

        except Exception as e:
            self.stderr.write(self.style.ERROR('Text recompilation failed: %s\n' % e))
            print_exc()

        else:
            self.stdout.write('Texts recompiled.\n')
