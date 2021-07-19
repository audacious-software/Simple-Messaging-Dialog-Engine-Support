# pylint: disable=no-member, line-too-long

from django.core.management.base import BaseCommand
from django.utils import timezone

from quicksilver.models import Task

class Command(BaseCommand):
    help = 'Sets up Quicksilver to run relevant dialog tasks.'

    def handle(self, *args, **options):
        send_messages = Task.objects.filter(command='simple_messaging_send_pending_messages', queue='default').first()

        if send_messages is None:
            send_messages = Task.objects.create(command='simple_messaging_send_pending_messages', repeat_interval=5, arguments='--no-color')
            send_messages.next_run = timezone.now()
            send_messages.save()

            print('Added "simple_messaging_send_pending_messages" task.')

        nudge_sessions = Task.objects.filter(command='nudge_active_sessions', queue='default').first()

        if nudge_sessions is None:
            nudge_sessions = Task.objects.create(command='nudge_active_sessions', repeat_interval=10, arguments='--no-color')
            nudge_sessions.next_run = timezone.now()
            nudge_sessions.save()

            print('Added "nudge_active_sessions" task.')

        clear_tasks = Task.objects.filter(command='clear_successful_executions', queue='default').first()

        if clear_tasks is None:
            clear_tasks = Task.objects.create(command='clear_successful_executions', repeat_interval=300, arguments='--no-color')
            clear_tasks.next_run = timezone.now()
            clear_tasks.save()

            print('Added "clear_successful_executions" task.')
