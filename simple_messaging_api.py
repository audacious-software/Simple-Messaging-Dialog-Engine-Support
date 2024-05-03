# pylint: disable=no-member, line-too-long

import json

from django.utils import timezone

from django_dialog_engine.models import Dialog, DialogScript

from .models import DialogSession, DialogTemplateVariable

def process_outgoing_message(outgoing_message, metadata=None): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    message_content = outgoing_message.current_message()

    if message_content.startswith('dialog:'): # pylint: disable=too-many-nested-blocks
        try:
            identifier = message_content.replace('dialog:', '')

            script = DialogScript.objects.filter(identifier=identifier).first()

            if script is not None:
                for session in DialogSession.objects.filter(finished=None):
                    if session.current_destination() == outgoing_message.current_destination():
                        session.finished = timezone.now()
                        session.save()

                        if session.dialog is not None:
                            session.dialog.finished = timezone.now()
                            session.dialog.finish_reason = 'dialog_cancelled'

                            session.dialog.save()

                script_def = script.definition

                metadata = {}

                script_labels = script.labels_list()

                template_variables = list(DialogTemplateVariable.objects.filter(script=None))
                template_variables.extend(script.template_variables.all())

                for variable in template_variables:
                    values = variable.value.strip().splitlines()

                    if len(values) == 1:
                        metadata[variable.key] = variable.value
                    else:
                        for raw_value in values:
                            value_tokens = raw_value.split('|')

                            if len(value_tokens) == 1:
                                metadata[variable.key] = value_tokens[0]
                            else:
                                tag = value_tokens[0]

                                if tag in script_labels:
                                    metadata[variable.key] = value_tokens[1]

                        if metadata.get(variable.key, None) is None:
                            value_tokens = values[0].split('|')

                            metadata[variable.key] = value_tokens[-1]

                if outgoing_message.message_metadata is not None and outgoing_message.message_metadata != '':
                    try:
                        metadata.update(json.loads(outgoing_message.message_metadata))

                        interrupt_minutes = metadata.get('interrupt_minutes', None)
                        pause_minutes = metadata.get('pause_minutes', None)
                        timeout_minutes = metadata.get('timeout_minutes', None)

                        for node in script_def:
                            if interrupt_minutes is not None and node['type'] == 'time-elapsed-interrupt':
                                node['type'] = 'pause'
                                node['duration'] = interrupt_minutes * 60

                            elif pause_minutes is not None and node['type'] == 'pause':
                                node['duration'] = pause_minutes * 60
                            elif timeout_minutes is not None and 'timeout' in node:
                                node['timeout'] = timeout_minutes * 60

                    except ValueError:
                        pass

                dialog = Dialog.objects.create(key=identifier, script=script, dialog_snapshot=script_def, started=timezone.now())

                if metadata is not None:
                    dialog.metadata = metadata
                    dialog.save()

                new_session = DialogSession.objects.create(destination=outgoing_message.current_destination(), dialog=dialog, started=dialog.started, last_updated=dialog.started)

                transmission_metadata = None

                try:
                    transmission_metadata = json.loads(outgoing_message.transmission_metadata)
                except ValueError:
                    transmission_metadata = {}
                except TypeError:
                    transmission_metadata = {}

                message_channel = transmission_metadata.get('message_channel', None)

                if message_channel is not None:
                    new_session.latest_variables['message_channel'] = message_channel
                    new_session.save()
                else: # Try to be explicit about channel if switchboard is present
                    try:
                        from simple_messaging_switchboard.models import Channel # pylint: disable=import-outside-toplevel

                        default_channel = Channel.objects.filter(is_default=True).first()

                        if default_channel is not None:
                            new_session.latest_variables['message_channel'] = default_channel.identifier
                            new_session.save()
                    except ImportError:
                        pass

                new_session.encrypt_destination()

                metadata = {
                    'session_id': new_session.pk
                }

                return metadata

            metadata = {
                'error': 'Unable to locate dialog %s.' % identifier
            }

            outgoing_message.errored = True

            return metadata
        except:
            traceback.print_exc()

    return None


def process_incoming_message(incoming_message):
    sender = incoming_message.current_sender()

    message_metadata = {}

    try:
        message_metadata = json.loads(incoming_message.transmission_metadata)
    except json.JSONDecodeError:
        pass

    session_channel = message_metadata.get('message_channel', None)

    for session in DialogSession.objects.filter(finished=None, transmission_channel=session_channel):
        if session.current_destination() == sender:
            processed = False

            try:
                from simple_messaging_switchboard.models import Channel # pylint: disable=import-outside-toplevel

                message_channel = None

                if session_channel is not None:
                    message_channel = Channel.objects.filter(identifier=session_channel, is_enabled=True).first()
                else:
                    message_channel = Channel.objects.filter(is_enabled=True, is_default=True).first()

                if message_channel is not None: # Found channel for session
                    extras = {
                        'message_channel': message_channel.identifier
                    }

                    session.process_response(incoming_message.message, transmission_extras=extras)

                    processed = True
                else:
                    processed = True # Skipping processing - message not associated with dialog w/ a channel

            except ImportError: # No switchboard installed...
                pass # traceback.print_exc()

            if processed is False:
                session.process_response(incoming_message.message)

def simple_messaging_record_response(post_request): # pylint: disable=invalid-name, unused-argument
    return True
