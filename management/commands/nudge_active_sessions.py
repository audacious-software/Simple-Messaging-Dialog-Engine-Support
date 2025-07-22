# pylint: disable=no-member

import logging
import traceback

from django.core.management import call_command
from django.core.management.base import BaseCommand

from quicksilver.decorators import handle_lock, handle_schedule, add_qs_arguments, handle_logging

from ...models import DialogSession

class Command(BaseCommand):
    help = 'Nudges ongoing dialog session to continue processing as needed'

    @add_qs_arguments
    def add_arguments(self, parser):
        pass

    @handle_logging
    @handle_schedule
    @handle_lock
    def handle(self, *args, **options):
        exception = None

        logger = options.get('_logger', None)

        if logger is None:
            logger = logging.getLogger(__name__)

        for session in DialogSession.objects.filter(finished=None):
            logger.info('Nudging session: %s', session)

            try:
                session.process_response(None, None, send_messages=False, logger=logger)
            except Exception as exc: # pylint: disable=bare-except, broad-exception-caught
                logger.error('Error encountered with session %s:', session.pk)
                logger.error(traceback.format_exc())

                exception = exc

        logger.debug('-' * 72)

        call_command('simple_messaging_send_pending_messages')

        if exception is not None:
            raise exception
