# pylint: disable=\no-member, line-too-long

from django.utils import timezone

from django_dialog_engine.models import Dialog, DialogScript

from .models import DialogSession

def process_outgoing_message(outgoing_message):
    message_text = outgoing_message.fetch_message(None)

    if message_text.startswith('dialog:'):
        identifier = message_text.replace('dialog:', '')

        script = DialogScript.objects.filter(identifier=identifier).first()

        if script is not None:
            for session in DialogSession.objects.filter(destination=outgoing_message.destination, finished=None):
                session.finished = timezone.now()
                session.save()

                if session.dialog is not None:
                    session.dialog.finished = timezone.now()
                    session.dialog.finish_reason = 'dialog_cancelled'

                    session.dialog.save()

            dialog = Dialog.objects.create(key=identifier, script=script, dialog_snapshot=script.definition, started=timezone.now())

            new_session = DialogSession.objects.create(destination=outgoing_message.destination, dialog=dialog, started=dialog.started, last_updated=dialog.started)

            metadata = {
                'session_id': new_session.pk
            }

            return metadata

    return None


def process_incoming_message(incoming_message):
    sender = incoming_message.sender

    for session in DialogSession.objects.filter(destination=sender, finished=None):
        session.process_response(incoming_message.message)


def simple_messaging_record_response(post_request): # pylint: disable=invalid-name
    sender = post_request['From']
    message = post_request['Body'].strip()

    if message.lower() == 'bws':
        for session in DialogSession.objects.filter(destination=sender, finished=None):
            session.finished = timezone.now()
            session.save()

            if session.dialog is not None:
                session.dialog.finished = timezone.now()
                session.dialog.finish_reason = 'dialog_cancelled'

                session.dialog.save()

        script = DialogScript.objects.filter(identifier='black-wall-street-journey').first()

        dialog = Dialog.objects.create(key='black-wall-street-journey', script=script, dialog_snapshot=script.definition, started=timezone.now())

        DialogSession.objects.create(destination=sender, dialog=dialog, started=dialog.started, last_updated=dialog.started)

    return True
