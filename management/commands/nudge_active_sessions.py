# pylint: disable=no-member, line-too-long

import importlib
import logging
import traceback

from django.conf import settings
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
            do_nudge = True

            session_variables = session.fetch_latest_variables()

            for app in settings.INSTALLED_APPS:
                if do_nudge:
                    try:
                        dialog_module = importlib.import_module('.dialog_api', package=app)

                        do_nudge = dialog_module.allow_session_nudge(session)
                    except ImportError:
                        pass # traceback.print_exc()
                    except AttributeError:
                        pass # traceback.print_exc()

            launch_keyword = session_variables.get('simple_messaging_launch_keyword', None)
            launch_keyword_consumed = session_variables.get('simple_messaging_launch_keyword_consumed', False)

            if launch_keyword is not None and launch_keyword_consumed is False:
                do_nudge = True

                session.add_variable('simple_messaging_launch_keyword_consumed', True)
            else:
                launch_keyword = None

            if do_nudge:
                logging.info('Nudging session: %s', session)

                try:
                    session.process_response(launch_keyword, None, send_messages=False, logger=logging.getLogger())
                except Exception as exc: # pylint: disable=bare-except, broad-exception-caught
                    logging.error('Error encountered with session %s:', session.pk)
                    logging.error(traceback.format_exc())

                    exception = exc
            else:
                logging.info('Skipping nudge for session: %s.', session.pk)

        logging.info('Open sessions nudged.')

        try:
            call_command('simple_messaging_send_pending_messages', '-v', '%s' % options.get('verbosity', -1))
        except: # pylint: disable=bare-except
            logging.error('Error encountered with command %s:', 'simple_messaging_send_pending_messages')
            logging.error(traceback.format_exc())

        logging.info('Wrapping up nudging. Exception? %s', exception)

        if exception is not None:
            raise exception

        logging.info('Nudge all done.')
