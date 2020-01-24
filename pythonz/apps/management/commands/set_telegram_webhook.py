from django.conf import settings
from django.core.management.base import BaseCommand

from ...integration.telegram import set_webhook, get_webhook_url


class Command(BaseCommand):

    help = 'Registers a webhook URL from Telegram Bot'

    def handle(self, *args, **options):

        self.stdout.write(f'Registering a webhook at {get_webhook_url()} ...')

        self_signed = settings.PATH_CERTIFICATE and settings.CERTIFICATE_SELF_SIGNED
        self.stdout.write(f"Using a self-signed certificate: {'TRUE' if self_signed else 'FALSE'}")

        set_webhook()

        self.stdout.write('All is done.\n')
