from django.core.management.base import BaseCommand

from ...commands import clean_missing_refs
from ...utils import get_logger


LOG = get_logger(__name__)


class Command(BaseCommand):

    help = 'Removes stale reference misses.'

    def handle(self, *args, **options):

        LOG.info('Cleaning reference misses ...')

        clean_missing_refs()

        LOG.info('Done')
