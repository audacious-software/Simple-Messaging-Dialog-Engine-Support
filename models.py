# pylint: disable=line-too-long, no-member
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

from builtins import str # pylint: disable=redefined-builtin

import importlib
import json
import traceback

from six import python_2_unicode_compatible

from django.conf import settings
from django.core.management import call_command
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import Template, Context
from django.utils import timezone

try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField

from django_dialog_engine.dialog import DialogError
from django_dialog_engine.models import Dialog, DialogScript

from simple_messaging.models import OutgoingMessage, encrypt_value, decrypt_value

class DialogSession(models.Model):
    destination = models.CharField(max_length=256)
    dialog = models.ForeignKey(Dialog, related_name='dialog_sessions', null=True, on_delete=models.SET_NULL)

    started = models.DateTimeField()
    last_updated = models.DateTimeField()
    finished = models.DateTimeField(null=True, blank=True)

    latest_variables = JSONField(default=dict)
    last_variable_update = models.DateTimeField(null=True, blank=True)

    transmission_channel = models.CharField(max_length=256, null=True, blank=True)

    def process_response(self, response, extras=None, transmission_extras=None, send_messages=True): # pylint: disable=too-many-branches, too-many-statements, too-many-locals
        message = None

        if transmission_extras is None:
            transmission_extras = {}

        if self.transmission_channel is None:
            if ('message_channel' in self.latest_variables) and ('message_channel' in transmission_extras) is False: # Add message channel if missing...
                transmission_extras['message_channel'] = self.latest_variables.get('message_channel')
        else:
            transmission_extras['message_channel'] = self.transmission_channel

        try:
            if isinstance(response, str):
                message = response
            elif response is not None:
                message = response.message

            if extras is None:
                extras = {}
        except: # pylint: disable=bare-except
            traceback.print_exc()

        for app in settings.INSTALLED_APPS:
            try:
                app_dialog_api = importlib.import_module(app + '.dialog_api')

                dest_variables = app_dialog_api.fetch_destination_variables(self.current_destination())

                if dest_variables is not None:
                    extras.update(dest_variables)
            except ImportError:
                pass
            except AttributeError:
                pass

        if message is not None:
            variable = DialogVariable.objects.create(sender=self.current_destination(), dialog_key=self.dialog.key, key='last_message', value=message, date_set=timezone.now())
            variable.encrypt_sender()

        extras.update(self.fetch_latest_variables())

        actions = self.dialog.process(message, extras)

        for app in settings.INSTALLED_APPS:
            try:
                app_dialog_api = importlib.import_module(app + '.dialog_api')

                app_dialog_api.update_destination_variables(self.current_destination(), extras)
            except ImportError:
                pass
            except AttributeError:
                pass

        if actions is not None: # pylint: disable=too-many-nested-blocks
            self.last_updated = timezone.now()

            for action in actions: # pylint: disable=unused-variable
                if 'type' in action:
                    if action['type'] == 'wait-for-input':
                        # Do nothing - input will come in via HTTP views...
                        pass
                    elif action['type'] == 'echo':
                        template = Template(action['message'])

                        rendered_message = template.render(Context(self.dialog.metadata))

                        message_metadata = {
                            'dialog_metadata': self.dialog.metadata
                        }

                        message = OutgoingMessage.objects.create(destination=self.destination, send_date=timezone.now(), message=rendered_message, message_metadata=json.dumps(message_metadata, indent=2), transmission_metadata=json.dumps(transmission_extras, indent=2))
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

                    elif action['type'] == 'alert' or action['type'] == 'raise-alert':
                        now = timezone.now()

                        alert = DialogAlert.objects.create(sender=self.current_destination(), dialog=self.dialog, message=action['message'], added=now, last_updated=now)
                        alert.encrypt_sender()

                        for app in settings.INSTALLED_APPS:
                            try:
                                app_dialog_api = importlib.import_module(app + '.dialog_api')

                                app_dialog_api.handle_dialog_alert(alert)
                            except ImportError:
                                pass
                            except AttributeError:
                                pass
                    else:
                        custom_action_found = False

                        for app in settings.INSTALLED_APPS:
                            if custom_action_found is False:
                                try:
                                    app_dialog_api = importlib.import_module(app + '.dialog_api')

                                    custom_action_found = app_dialog_api.execute_dialog_action(self.current_destination(), extras, action)
                                except ImportError:
                                    pass
                                except AttributeError:
                                    pass

                        if custom_action_found is False:
                            raise DialogError('Unknown action: %s' % json.dumps(action))
                else:
                    raise DialogError('Unknown action: %s' % json.dumps(action))

        if self.dialog.finished is not None:
            self.finished = self.dialog.finished

        self.save()

        if send_messages:
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
        query = Q(dialog_key=self.dialog.key)

        variables = self.latest_variables

        if self.finished is not None:
            if self.last_variable_update is not None and self.last_variable_update > self.finished:
                return variables

            query = query & Q(date_set__lte=self.finished)

        if self.last_variable_update is not None:
            query = query & Q(date_set__gte=self.last_variable_update)

        current_dest = self.current_destination()

        for variable in DialogVariable.objects.filter(query).order_by('date_set'):
            if variable.current_sender() == current_dest:
                variables[variable.key] = variable.value

        self.latest_variables = variables
        self.last_variable_update = timezone.now()
        self.save()

        return variables

    def add_variable(self, key, value, dialog_key=None):
        DialogVariable.objects.create(sender=self.current_destination(), dialog_key=dialog_key, key=key, value=value, date_set=timezone.now())

    def cancel_sesssion(self):
        if self.dialog.is_active():
            self.dialog.finish(finish_reason='user_cancelled')
            self.last_updated = timezone.now()
            self.save()

@receiver(post_save, sender=DialogSession)
def update_dialog_variables(sender, instance, created, raw, using, update_fields, **kwargs): # pylint: disable=too-many-arguments, too-many-locals, unused-argument, too-many-branches
    if created is True and raw is False: # pylint: disable=too-many-nested-blocks
        template_variables = list(DialogTemplateVariable.objects.filter(script=None))

        script_labels = []

        if instance.dialog.script:
            template_variables.extend(instance.dialog.script.template_variables.all())

            script_labels = instance.dialog.script.labels_list()

        for variable in template_variables:
            if (variable.key in instance.dialog.metadata) is False:
                values = variable.value.strip().splitlines()

                if len(values) == 1:
                    instance.dialog.metadata[variable.key] = variable.value
                else:
                    for raw_value in values:
                        value_tokens = raw_value.split('|')

                        if len(value_tokens) == 1:
                            instance.dialog.metadata[variable.key] = value_tokens[0]
                        else:
                            tag = value_tokens[0]

                            if tag in script_labels:
                                instance.dialog.metadata[variable.key] = value_tokens[1]

                    if instance.dialog.metadata.get(variable.key, None) is None:
                        value_tokens = values[0].split('|')

                        instance.dialog.metadata[variable.key] = value_tokens[-1]

        for app in settings.INSTALLED_APPS:
            try:
                app_dialog_api = importlib.import_module(app + '.dialog_api')

                updates = app_dialog_api.fetch_dialog_metadata(instance.current_destination(), instance.dialog)

                instance.dialog.metadata.update(updates)
            except ImportError:
                pass
            except AttributeError:
                pass

        instance.dialog.save()

@python_2_unicode_compatible
class DialogVariable(models.Model):
    sender = models.CharField(max_length=256)
    dialog_key = models.CharField(max_length=256, null=True, blank=True, db_index=True)

    key = models.CharField(max_length=1024, db_index=True)
    value = models.TextField(max_length=4194304)

    date_set = models.DateTimeField(db_index=True)

    lookup_hash = models.CharField(max_length=1024, null=True, blank=True)

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

    def __str__(self):
        return '%s.%s[%s] = %s (%s)' % (self.dialog_key, self.key, self.current_sender(), self.value, self.date_set)

@python_2_unicode_compatible
class DialogTemplateVariable(models.Model):
    script = models.ForeignKey(DialogScript, related_name='template_variables', null=True, blank=True, on_delete=models.SET_NULL)
    key = models.CharField(max_length=1024)
    value = models.TextField(max_length=4194304)

    def __str__(self):
        return '%[s] %s = %s' % (self.script, self.key, self.value)

@python_2_unicode_compatible
class DialogAlert(models.Model):
    sender = models.CharField(max_length=256)
    dialog = models.ForeignKey(Dialog, related_name='dialog_alerts', null=True, on_delete=models.SET_NULL)

    message = models.TextField(max_length=(1024 * 1024)) # pylint: disable=superfluous-parens

    added = models.DateTimeField()
    last_updated = models.DateTimeField()

    metadata = JSONField(null=True, blank=True)

    def __str__(self):
        return '%s[s]: %s (%s / %s)' % (self.current_sender(), self.dialog, self.message, self.added)

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

    def is_unread(self):
        if self.metadata is None:
            return True

        return self.metadata.get('read_time', None) is None

    def set_read(self, when):
        metadata = self.metadata

        if metadata is None:
            metadata = {}

        metadata['read_time'] = when.isoformat()

        self.metadata = metadata

        self.save()
