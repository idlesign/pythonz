from django.core.management.base import BaseCommand

from ...realms import get_realm


class Command(BaseCommand):

    help = 'Generates slugs for given realm model'
    args = '[realm_name realm_name ...]'

    def handle(self, *realm_names: str, **options):

        self.stdout.write('Starting slugs generation ...\n')

        for realm_name in realm_names:

            realm = get_realm(realm_name)

            if realm is None:
                self.stderr.write(self.style.ERROR(f'Unknown realm: {realm_name}\n'))

            else:
                model_cls = realm.model
                if hasattr(model_cls, 'autogenerate_slug'):

                    self.stdout.write(f'Processing {model_cls.__name__} model ...\n')

                    realm_iface = hasattr(model_cls, 'mark_unmodified')
                    for obj in model_cls.objects.all():

                        if realm_iface:
                            obj.mark_unmodified()

                        self.stdout.write(f'Processing {obj} ...\n')
                        obj.save()

                else:
                    self.stderr.write(self.style.ERROR(f'{model_cls} has no slug support.\n'))

        self.stdout.write('All is done.\n')
