# pylint: disable=no-member, line-too-long

import json

from django.utils import timezone

from django_dialog_engine.models import Dialog, DialogScript

from .models import DialogSession

def process_outgoing_message(outgoing_message):
    if outgoing_message.message.startswith('dialog:'): # pylint: disable=too-many-nested-blocks
        identifier = outgoing_message.message.replace('dialog:', '')

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

            if outgoing_message.message_metadata is not None and outgoing_message.message_metadata != '':
                try:
                    metadata = json.loads(outgoing_message.message_metadata)

                    interrupt_minutes = metadata.get('interrupt_minutes', None)
                    pause_minutes = metadata.get('pause_minutes', None)

                    for node in script_def:
                        if interrupt_minutes is not None and node['type'] == 'time-elapsed-interrupt':
                            node['hours_elapsed'] = int(interrupt_minutes / 60)
                            node['minutes_elapsed'] = int(interrupt_minutes % 60)

                        if pause_minutes is not None and node['type'] == 'pause':
                            node['duration'] = pause_minutes * 60
                except json.decoder.JSONDecodeError:
                    pass

            dialog = Dialog.objects.create(key=identifier, script=script, dialog_snapshot=script_def, started=timezone.now())

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
