# pylint: disable=no-member, line-too-long

from django.core.management import call_command
from django.core.management.base import BaseCommand

from quicksilver.decorators import handle_lock

from ...models import DialogSession, DialogVariable

class Command(BaseCommand):
    help = 'Encrypts any cleartext phone numbers if suitable key is present.'

    @handle_lock
    def handle(self, *args, **options):
        call_command('simple_messaging_encrypt_addresses')

        for session in DialogSession.objects.all():
            session.encrypt_destination()

        for variable in DialogVariable.objects.all():
            variable.encrypt_sender()
