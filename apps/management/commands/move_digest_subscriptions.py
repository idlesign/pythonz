from django.core.management.base import BaseCommand
from sitemessage.models import Subscription

from ...models import User


class Command(BaseCommand):

    help = 'Migrates digest subscriptions handling from pythonz to sitemessages'

    def handle(self, *args, **options):

        self.stdout.write('Starting migration ...\n')
        try:
            subscribers = User.objects.filter(digest_enabled=True).values_list('id', flat=True)
            targets = []
            for subscriber in subscribers:
                targets.append(Subscription(
                    message_cls='digest',
                    messenger_cls='smtp',
                    recipient_id=subscriber
                ))
                self.stdout.write('User ID %s subscribed ...\n' % subscriber)

            Subscription.objects.bulk_create(targets)

        except Exception as e:
            self.stderr.write(self.style.ERROR('Migration failed: %s\n' % e))

        else:
            self.stdout.write('All is done. Total subscribers: %s\n' % len(targets))
