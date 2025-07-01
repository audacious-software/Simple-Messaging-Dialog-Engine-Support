# pylint: disable=no-member, line-too-long

import json

try:
    from collections import UserDict
except ImportError:
    from UserDict import UserDict

from django.utils import timezone

from simple_messaging.models import OutgoingMessage

from .models import DialogVariable

def store_value(sender, dialog_key, key, value):
    value_obj = {
        'value': value
    }

    if isinstance(value, (UserDict, dict)):
        if value.get('value', None) is not None:
            value_obj = value

    variable = DialogVariable.objects.create(sender=sender, dialog_key=dialog_key, key=key, value='json:%s' % json.dumps(value_obj), date_set=timezone.now())
    variable.encrypt_sender()

def update_value(sender, dialog_key, key, value, operation, replacement): # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
    last_variable = None

    if (operation in ('clear-list', 'set',)) is False:
        for variable in DialogVariable.objects.filter(dialog_key=dialog_key, key=key).order_by('-date_set'):
            if variable.current_sender() == sender:
                last_variable = variable

                break

    if operation == 'clear-list':
        store_value(sender, dialog_key, key, [])
    elif operation == 'set':
        store_value(sender, dialog_key, key, value)
    elif operation == 'append-list':
        last_value = []

        if last_variable is not None:
            last_value = last_variable.fetch_value().get('value', [])

        if isinstance(last_value, list) is False:
            last_value = [last_value]

        last_value.append(value)

        store_value(sender, dialog_key, key, last_value)
    elif operation == 'prepend-list':
        last_value = []

        if last_variable is not None:
            last_value = last_variable.fetch_value().get('value', [])

        if isinstance(last_value, list) is False:
            last_value = [last_value]

        last_value.insert(0, value)

        store_value(sender, dialog_key, key, last_value)
    elif operation == 'remove':
        last_value = []

        if last_variable is not None:
            last_value = last_variable.fetch_value().get('value', [])

        updated = False

        if isinstance(last_value, str):
            last_value = last_value.replace(value, '')

            updated = True
        elif isinstance(last_value, list):
            last_value = [item for item in last_value if item != value]

            updated = True

        if updated:
            store_value(sender, dialog_key, key, last_value)
    elif operation == 'replace':
        last_value = []

        if last_variable is not None:
            last_value = last_variable.fetch_value().get('value', [])

        updated = False

        if isinstance(last_value, str):
            last_value = last_value.replace(value, replacement)

            updated = True
        elif isinstance(last_value, list):
            while value in last_value:
                value_index = last_value.index(value)

                last_value[value_index] = replacement

            updated = True

        if updated:
            store_value(sender, dialog_key, key, last_value)
    elif operation == 'increment':
        last_value = []

        if last_variable is not None:
            last_value = last_variable.fetch_value().get('value', [])

        increment_value = 0

        try:
            increment_value = float(value)
        except ValueError:
            try:
                increment_value = int(value)
            except ValueError:
                pass

        updated = False

        if isinstance(last_value, (int, float)):
            last_value = last_value + increment_value

            updated = True
        elif isinstance(last_value, list):
            for item_index in range(0, len(last_value)): # pylint: disable=consider-using-enumerate
                item = last_value[item_index]

                try:
                    float_item = float(item)

                    item = float_item + increment_value

                except ValueError:
                    try:
                        int_item = float(item)

                        item = int_item + increment_value
                    except ValueError:
                        pass

                last_value[item_index] = item

            updated = True

        if updated:
            store_value(sender, dialog_key, key, last_value)

def fetch_destination_variables(destination): # pylint: disable=unused-argument
    return None

def dialog_builder_cards():
    return [
        ('Start New Session', 'start-new-session',),
    ]

def launch_dialog_script(identifier, destination):
    outgoing = OutgoingMessage.objects.create(destination=destination, send_date=timezone.now(), message='dialog:%s' % identifier)

    outgoing.encrypt_destination()
    outgoing.encrypt_message()

    return True
