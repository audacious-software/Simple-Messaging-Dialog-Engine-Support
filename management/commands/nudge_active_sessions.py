# pylint: disable=no-member

import traceback

import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand

from quicksilver.decorators import handle_lock, handle_schedule, add_qs_arguments

from ...models import DialogSession

class Command(BaseCommand):
    help = 'Nudges ongoing dialog session to continue processing as needed'

    @add_qs_arguments
    def add_arguments(self, parser):
        pass

    @handle_lock
    @handle_schedule
    def handle(self, *args, **options):
        for session in DialogSession.objects.filter(finished=None):
            try:
                session.process_response(None, None, send_messages=False)
            except:
                logging.error('Error encountered with session %s:', session.pk)
                logging.error(traceback.format_exc())

        call_command('simple_messaging_send_pending_messages')
