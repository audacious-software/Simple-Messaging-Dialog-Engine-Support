# pylint: disable=no-member, line-too-long

import json

from django.utils import timezone

from django_dialog_engine.models import Dialog, DialogScript

from .models import DialogSession, DialogTemplateVariable

def process_outgoing_message(outgoing_message): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    message_content = outgoing_message.current_message()

    if message_content.startswith('dialog:'): # pylint: disable=too-many-nested-blocks
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
                            node['hours_elapsed'] = int(interrupt_minutes / 60)
                            node['minutes_elapsed'] = int(interrupt_minutes % 60)

                        if pause_minutes is not None and node['type'] == 'pause':
                            node['duration'] = pause_minutes * 60

                        if timeout_minutes is not None and 'timeout' in node:
                            node['timeout'] = timeout_minutes * 60

                except json.decoder.JSONDecodeError:
                    pass

            dialog = Dialog.objects.create(key=identifier, script=script, dialog_snapshot=script_def, started=timezone.now())

            if metadata is not None:
                dialog.metadata = metadata
                dialog.save()

            new_session = DialogSession.objects.create(destination=outgoing_message.current_destination(), dialog=dialog, started=dialog.started, last_updated=dialog.started)
            new_session.encrypt_destination()

            metadata = {
                'session_id': new_session.pk
            }

            return metadata

    return None


def process_incoming_message(incoming_message):
    sender = incoming_message.current_sender()

    for session in DialogSession.objects.filter(finished=None):
        if session.current_destination() == sender:
            session.process_response(incoming_message.message)

def simple_messaging_record_response(post_request): # pylint: disable=invalid-name, unused-argument
    return True
