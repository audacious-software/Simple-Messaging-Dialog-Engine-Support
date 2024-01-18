# pylint: disable=no-member, line-too-long

import json

from django.utils import timezone

from .models import DialogVariable

def store_value(sender, dialog_key, key, value):
    variable = DialogVariable.objects.create(sender=sender, dialog_key=dialog_key, key=key, value=value, date_set=timezone.now())
    variable.encrypt_sender()

def update_value(sender, dialog_key, key, value, operation, replacement):

    if operation == 'clear-list':
        store_value(sender, dialog_key, key, 'json:[]')
    elif operation == 'append-list':
        last_variable = DialogVariable.objects.filter(sender=sender, dialog_key=dialog_key, key=key).order_by('-date_set').first()

        last_value = 'json:[]'

        if last_variable is not None:
            last_value = last_variable.value

        parsed = []

        try:
            parsed = json.loads(last_value[:5])
        except:
            pass

        parsed.append(value)

        store_value(sender, dialog_key, key, 'json:%s' % json.dumps(parse))


def fetch_destination_variables(destination): # pylint: disable=unused-argument
    return None
