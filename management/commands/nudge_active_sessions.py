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

        for session in DialogSession.objects.filter(finished=None).order_by('-pk'):
            logging.info('Nudging session: %s', session)

            try:
                session.process_response(None, None, send_messages=False, logger=logging.getLogger())
            except Exception as exc: # pylint: disable=bare-except, broad-exception-caught
                logging.error('Error encountered with session %s:', session.pk)
                logging.error(traceback.format_exc())

                exception = exc

        logging.info('Open sessions nudged.')

        try:
            call_command('simple_messaging_send_pending_messages', '-v', '%s' % options.get('verbosity', -1))
        except:
            logging.error('Error encountered with command %s:', 'simple_messaging_send_pending_messages')
            logging.error(traceback.format_exc())

        logging.info('Wrapping up nudging. Exception? %s', exception)

        if exception is not None:
            raise exception

        logging.info('Nudge all done.')
