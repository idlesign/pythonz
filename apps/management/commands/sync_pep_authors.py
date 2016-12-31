from django.core.management.base import BaseCommand

from ...integration.peps import sync
from ...utils import get_logger


LOG = get_logger(__name__)


class Command(BaseCommand):

    help = 'Updates persons from PEP authors'

    def handle(self, *args, **options):

        LOG.info('Updating persons ...')

        sync(skip_deadend_peps=False)

        LOG.info('Updating persons done')
