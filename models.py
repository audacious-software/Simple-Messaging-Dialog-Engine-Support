# pylint: disable=line-too-long, no-member
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

from builtins import str # pylint: disable=redefined-builtin

import importlib
import json
import traceback

from django.conf import settings
from django.core.management import call_command
from django.db import models
from django.db.models import Q
from django.utils import timezone

from django_dialog_engine.models import Dialog
from simple_messaging.models import OutgoingMessage, encrypt_value, decrypt_value

class DialogSession(models.Model):
    destination = models.CharField(max_length=256)
    dialog = models.ForeignKey(Dialog, related_name='dialog_sessions', null=True, on_delete=models.SET_NULL)

    started = models.DateTimeField()
    last_updated = models.DateTimeField()
    finished = models.DateTimeField(null=True, blank=True)

    def process_response(self, response, extras=None): # pylint: disable=too-many-branches
        message = None

        try:
            if isinstance(response, str):
                message = response
            elif response is not None:
                message = response.message

            if extras is None:
                extras = {}
        except: # pylint: disable=bare-except
            traceback.print_exc()

        extras.update(self.fetch_latest_variables())

        actions = self.dialog.process(message, extras)

        if actions is not None: # pylint: disable=too-many-nested-blocks
            self.last_updated = timezone.now()

            for action in actions: # pylint: disable=unused-variable
                if 'type' in action:
                    if action['type'] == 'wait-for-input':
                        # Do nothing - input will come in via HTTP views...
                        pass
                    elif action['type'] == 'echo':
                        message = OutgoingMessage.objects.create(destination=self.destination, send_date=timezone.now(), message=action['message'])
                        message.encrypt_destination()
                    elif action['type'] == 'pause':
                        # Do nothing - pause will conclude in a subsequent call
                        pass
                    elif action['type'] == 'store-value':
                        for app in settings.INSTALLED_APPS:
                            try:
                                app_dialog_api = importlib.import_module(app + '.dialog_api')

                                app_dialog_api.store_value(self.current_destination(), self.dialog.key, action['key'], action['value'])
                            except ImportError:
                                pass
                            except AttributeError:
                                pass
                    elif action['type'] == 'external-choice':
                        pass # Do nothing - waiting for external choice to be made...

                    elif action['type'] == 'alert':
                        print('ALERT(TODO): %s' % json.dumps(action, indent=2))
                    else:
                        raise Exception('Unknown action: ' + json.dumps(action))
                else:
                    raise Exception('Unknown action: ' + json.dumps(action))

        if self.dialog.finished is not None:
            self.finished = self.dialog.finished

        self.save()

        call_command('simple_messaging_send_pending_messages')

    def current_destination(self):
        if self.destination is not None and self.destination.startswith('secret:'):
            return decrypt_value(self.destination)

        return self.destination

    def update_destination(self, new_destination, force=False):
        if force is False and new_destination == self.current_destination():
            return # Same as current - don't add

        if hasattr(settings, 'SIMPLE_MESSAGING_SECRET_KEY'):
            encrypted_dest = encrypt_value(new_destination)

            self.destination = encrypted_dest
        else:
            self.destination = new_destination

        self.save()

    def encrypt_destination(self):
        if self.destination.startswith('secret:') is False:
            self.update_destination(self.destination, force=True)

    def fetch_latest_variables(self):
        query = Q(dialog_key=self.dialog.key) & Q(date_set__gte=self.started)

        variables = {}

        if self.finished is not None:
            query = query & Q(date_set__lte=self.finished)

        current_dest = self.current_destination()

        for variable in DialogVariable.objects.filter(query).order_by('date_set'):
            if variable.current_sender() == current_dest:
                variables[variable.key] = variable.value

        return variables

class DialogVariable(models.Model):
    sender = models.CharField(max_length=256)
    dialog_key = models.CharField(max_length=256, null=True, blank=True)

    key = models.CharField(max_length=1024)
    value = models.TextField(max_length=4194304)

    date_set = models.DateTimeField()

    def value_truncated(self):
        if len(self.value) > 64:
            return self.value[:64] + '...' # pylint: disable=unsubscriptable-object

        return self.value

    def current_sender(self):
        if self.sender is not None and self.sender.startswith('secret:'):
            return decrypt_value(self.sender)

        return self.sender

    def update_sender(self, new_sender, force=False):
        if force is False and new_sender == self.current_sender():
            return # Same as current - don't add

        if hasattr(settings, 'SIMPLE_MESSAGING_SECRET_KEY'):
            encrypted_sender = encrypt_value(new_sender)

            self.sender = encrypted_sender
        else:
            self.sender = new_sender

        self.save()

    def encrypt_sender(self):
        if self.sender.startswith('secret:') is False:
            self.update_sender(self.sender, force=True)
