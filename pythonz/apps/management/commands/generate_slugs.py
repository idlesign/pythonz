from django.core.management.base import BaseCommand

from ...realms import get_realm


class Command(BaseCommand):

    help = 'Generates slugs for given realm model'
    args = '[realm_name realm_name ...]'

    def handle(self, *realm_names, **options):

        self.stdout.write('Starting slugs generation ...\n')

        for realm_name in realm_names:

            realm = get_realm(realm_name)
            if realm is None:
                self.stderr.write(self.style.ERROR('Unknown realm: %s\n' % realm_name))

            else:
                model_cls = realm.model
                if hasattr(model_cls, 'autogenerate_slug'):

                    self.stdout.write('Processing %s model ...\n' % model_cls.__name__)

                    realm_iface = hasattr(model_cls, 'mark_unmodified')
                    for obj in model_cls.objects.all():

                        if realm_iface:
                            obj.mark_unmodified()

                        self.stdout.write('Processing %s ...\n' % obj)
                        obj.save()

                else:
                    self.stderr.write(self.style.ERROR('%s has no slug support.\n'))

        self.stdout.write('All is done.\n')
