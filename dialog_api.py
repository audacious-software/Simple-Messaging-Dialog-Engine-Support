# pylint: disable=no-member, line-too-long

import json
import traceback

from django.utils import timezone

from .models import DialogVariable

def store_value(sender, dialog_key, key, value):
    variable = DialogVariable.objects.create(sender=sender, dialog_key=dialog_key, key=key, value=value, date_set=timezone.now())
    variable.encrypt_sender()

def update_value(sender, dialog_key, key, value, operation, replacement): # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
    last_variable = None

    if (operation in ('clear-list', 'set',)) is False:
        for variable in DialogVariable.objects.filter(dialog_key=dialog_key, key=key).order_by('-date_set'):
            if variable.current_sender() == sender:
                last_variable = variable

                break

    if operation == 'clear-list':
        store_value(sender, dialog_key, key, 'json:[]')
    elif operation == 'set':
        store_value(sender, dialog_key, key, 'json:%s' % json.dumps(value))
    elif operation == 'append-list':
        last_value = 'json:[]'

        if last_variable is not None:
            last_value = last_variable.value

        parsed = []

        try:
            parsed = json.loads(last_value[5:])
        except json.JSONDecodeError:
            traceback.print_exc() # pass

        if isinstance(parsed, list) is False:
            parsed = [parsed]

        parsed.append(value)

        store_value(sender, dialog_key, key, 'json:%s' % json.dumps(parsed))
    elif operation == 'prepend-list':
        last_value = 'json:[]'

        if last_variable is not None:
            last_value = last_variable.value

        parsed = []

        try:
            parsed = json.loads(last_value[5:])
        except json.JSONDecodeError:
            traceback.print_exc() # pass

        if isinstance(parsed, list) is False:
            parsed = [parsed]

        parsed.insert(0, value)

        store_value(sender, dialog_key, key, 'json:%s' % json.dumps(parsed))
    elif operation == 'remove':
        last_value = 'json:[]'

        if last_variable is not None:
            last_value = last_variable.value

        parsed = []

        try:
            parsed = json.loads(last_value[5:])
        except json.JSONDecodeError:
            traceback.print_exc() # pass

        updated = False

        if isinstance(parsed, str):
            parsed = parsed.replace(value, '')

            updated = True
        elif isinstance(parsed, list):
            parsed = [item for item in parsed if item != value]

            updated = True

        if updated:
            store_value(sender, dialog_key, key, 'json:%s' % json.dumps(parsed))
    elif operation == 'replace':
        last_value = 'json:[]'

        if last_variable is not None:
            last_value = last_variable.value

        parsed = []

        try:
            parsed = json.loads(last_value[5:])
        except json.JSONDecodeError:
            traceback.print_exc() # pass

        updated = False

        if isinstance(parsed, str):
            parsed = parsed.replace(value, replacement)

            updated = True
        elif isinstance(parsed, list):
            while value in parsed:
                value_index = parsed.index(value)

                parsed[value_index] = replacement

            updated = True

        if updated:
            store_value(sender, dialog_key, key, 'json:%s' % json.dumps(parsed))
    elif operation == 'increment':
        last_value = 'json:[]'

        if last_variable is not None:
            last_value = last_variable.value

        parsed = []

        try:
            parsed = json.loads(last_value[5:])
        except json.JSONDecodeError:
            traceback.print_exc() # pass

        increment_value = 0

        try:
            increment_value = float(value)
        except ValueError:
            try:
                increment_value = int(value)
            except ValueError:
                pass

        updated = False

        if isinstance(parsed, (int, float)):
            parsed = parsed + increment_value

            updated = True
        elif isinstance(parsed, list):
            for item_index in range(0, len(parsed)): # pylint: disable=consider-using-enumerate
                item = parsed[item_index]

                try:
                    float_item = float(item)

                    item = float_item + increment_value

                except ValueError:
                    try:
                        int_item = float(item)

                        item = int_item + increment_value
                    except ValueError:
                        pass

                parsed[item_index] = item

            updated = True

        if updated:
            store_value(sender, dialog_key, key, 'json:%s' % json.dumps(parsed))

def fetch_destination_variables(destination): # pylint: disable=unused-argument
    return None

def dialog_builder_cards():
    return [
        ('Start New Session', 'start-new-session',),
    ]
