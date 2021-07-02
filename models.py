# pylint: disable=line-too-long, no-member
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import importlib
import json

from django.conf import settings
from django.core.management import call_command
from django.db import models
from django.utils import timezone

from django_dialog_engine.models import Dialog
from simple_messaging.models import OutgoingMessage

class DialogSession(models.Model):
    destination = models.CharField(max_length=256)
    dialog = models.ForeignKey(Dialog, related_name='dialog_sessions', null=True, on_delete=models.SET_NULL)

    started = models.DateTimeField()
    last_updated = models.DateTimeField()
    finished = models.DateTimeField(null=True, blank=True)

    def process_response(self, response, extras=None): # pylint: disable=too-many-branches
        message = None

        if isinstance(response, str):
            message = response
        elif response is not None:
            message = response.message

        actions = self.dialog.process(message, extras)

        if actions is not None: # pylint: disable=too-many-nested-blocks
            self.last_updated = timezone.now()

            for action in actions: # pylint: disable=unused-variable
                if 'type' in action:
                    if action['type'] == 'wait-for-input':
                        # Do nothing - input will come in via HTTP views...
                        pass
                    elif action['type'] == 'echo':
                        OutgoingMessage.objects.create(destination=self.destination, send_date=timezone.now(), message=action['message'])
                    elif action['type'] == 'pause':
                        # Do nothing - pause will conclude in a subsequent call
                        pass
                    elif action['type'] == 'store-value':
                        for app in settings.INSTALLED_APPS:
                            try:
                                app_dialog_api = importlib.import_module(app + '.dialog_api')

                                app_dialog_api.store_value(self.destination, self.dialog.key, action['key'], action['value'])
                            except ImportError:
                                pass
                            except AttributeError:
                                pass
                    elif action['type'] == 'external-choice':
                        pass # Do nothing - waiting for external choice to be made...
                    else:
                        raise Exception('Unknown action: ' + json.dumps(action))
                else:
                    raise Exception('Unknown action: ' + json.dumps(action))

        if self.dialog.finished is not None:
            self.finished = self.dialog.finished

        self.save()

        call_command('simple_messaging_send_pending_messages')

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
