# pylint: disable=line-too-long, no-member

import importlib
import io
import hashlib
import os
import tempfile

import pytz

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from simple_data_export.utils import fetch_export_identifier, UnicodeWriter # pylint: disable=import-error

from .models import DialogSession, DialogVariable

def export_data_sources(params=None):
    if params is None:
        params = {}

    destinations = []

    for session in DialogSession.objects.all():
        destination = session.current_destination()

        if (destination in destinations) is False:
            destinations.append(destination)

    return destinations

def export_data_types():
    return [
        ('simple_messaging_dialog_support.dialog_variables', 'Session Dialog Variables',),
        ('simple_messaging_dialog_support.dialog_variable_timeline', 'Dialog Variable Timeline',),
    ]

def compile_data_export(data_type, data_sources, start_time=None, end_time=None, custom_parameters=None): # pylint: disable=too-many-locals, unused-argument, too-many-branches, too-many-statements
    here_tz = pytz.timezone(settings.TIME_ZONE)

    if data_type == 'simple_messaging_dialog_support.dialog_variables':
        filename = tempfile.gettempdir() + os.path.sep + 'simple_messaging_dialog_support.dialog_variables.txt'

        print('simple_messaging_dialog_support.dialog_variables: 1')

        with io.open(filename, 'wb') as outfile:
            print('simple_messaging_dialog_support.dialog_variables: 1.1')

            writer = UnicodeWriter(outfile, delimiter='\t')

            variables = [
                'Destination',
                'Dialog',
                'Started',
                'Finished',
                'Cancelled',
            ]

            dialog_variables = []

            print('simple_messaging_dialog_support.dialog_variables: 1.2')

            for app in settings.INSTALLED_APPS:
                try:
                    app_dialog_api = importlib.import_module(app + '.dialog_api')

                    specific_variables = app_dialog_api.dialog_export_variables(None)

                    if specific_variables is not None:
                        dialog_variables.extend(specific_variables)
                except ImportError:
                    pass
                except AttributeError:
                    pass

            print('simple_messaging_dialog_support.dialog_variables: 1.3')

            if len(dialog_variables) == 0: # pylint: disable=len-as-condition
                for variable_key in DialogVariable.objects.order_by().values_list('key', flat=True).distinct():
                    if (variable_key in dialog_variables) is False:
                        dialog_variables.append(variable_key)

            variables.extend(dialog_variables)

            print('simple_messaging_dialog_support.dialog_variables: 1.4')

            writer.writerow(variables)

            print('simple_messaging_dialog_support.dialog_variables: 1.5')

            for session in DialogSession.objects.exclude(finished=None).order_by('started'): # pylint: disable=too-many-nested-blocks
                destination = session.current_destination()

                if destination in data_sources:
                    print('simple_messaging_dialog_support.dialog_variables[%s]: 1.5.1' % destination)

                    if session.dialog is not None:
                        print('simple_messaging_dialog_support.dialog_variables[%s]: 1.5.1.1' % destination)

                        session_variables = {
                            'Destination': fetch_export_identifier(destination),
                            'Dialog': session.dialog.key,
                            'Started': session.started.astimezone(here_tz).isoformat(),
                            'Finished': session.finished.astimezone(here_tz).isoformat(),
                            'Cancelled': False,
                        }

                        if session.dialog.finish_reason in ('user_cancelled', 'dialog_cancelled', 'timed_out',):
                            session_variables['Cancelled'] = True

                        print('simple_messaging_dialog_support.dialog_variables[%s]: 1.5.1.2' % destination)

                        query = Q(lookup_hash=None)

                        hash_obj = hashlib.sha256()
                        hash_obj.update(destination.encode('utf-8'))

                        hash_lookup = hash_obj.hexdigest()

                        query = query | Q(lookup_hash=hash_lookup)

                        query = query & Q(date_set__gte=session.started)
                        query = query & Q(date_set__lte=session.finished)

                        print('simple_messaging_dialog_support.dialog_variables[%s]: 1.5.1.3' % destination)

                        variable_pks = DialogVariable.objects.filter(query).order_by('date_set').values_list('pk', flat=True)

                        index = 0

                        print('simple_messaging_dialog_support.dialog_variables[%s]: 1.5.1.4 - %s' % (destination, len(variable_pks)))

                        for variable_pk in variable_pks: # in DialogVariable.objects.order_by('date_set'):
                            if (index % 500) == 0:
                                print('simple_messaging_dialog_support.dialog_variables[%s]: %s / %s -- %s' % (destination, index, len(variable_pks), timezone.now().isoformat()))

                            index += 1

                            variable = DialogVariable.objects.get(pk=variable_pk)

                            sender = variable.current_sender()

                            hash_obj = hashlib.sha256()
                            hash_obj.update(sender.encode('utf-8'))

                            hash_lookup = hash_obj.hexdigest()

                            if sender == destination:
                                if (variable.key in session_variables) is False:
                                    session_variables[variable.key] = []

                                session_variables[variable.key].append(str(variable.fetch_value()))

                            if variable.lookup_hash is None:
                                variable.lookup_hash = hash_lookup
                                variable.save()

                        row = []

                        for variable in variables:
                            if variable in session_variables:
                                value = session_variables[variable]

                                if isinstance(value, list):
                                    row.append('; '.join(value))
                                elif isinstance(value, bool):
                                    row.append(str(value))
                                else:
                                    row.append(value)
                            else:
                                row.append('')

                        writer.writerow(row)

        return filename

    if data_type == 'simple_messaging_dialog_support.dialog_variable_timeline':
        filename = tempfile.gettempdir() + os.path.sep + 'simple_messaging_dialog_support.dialog_variables.txt'

        print('dialog_variable_timeline 1.1')

        with io.open(filename, 'wb') as outfile:
            writer = UnicodeWriter(outfile, delimiter='\t')

            columns = [
                'Destination',
                'Dialog',
                'Date Set',
                'Key',
                'Value',
            ]

            print('dialog_variable_timeline 1.1.2')

            writer.writerow(columns)

            for data_source in data_sources:
                print('dialog_variable_timeline 1.1.2 -- %s' % data_source)

                source_names = [data_source]

                export_name = fetch_export_identifier(data_source)

                if export_name != data_source:
                    source_names.append(export_name)

                query = Q(lookup_hash=None)

                for source_name in source_names:
                    hash_obj = hashlib.sha256()
                    hash_obj.update(source_name.encode('utf-8'))

                    hash_lookup = hash_obj.hexdigest()

                    query = query | Q(lookup_hash=hash_lookup) # pylint: disable=unsupported-binary-operation

                variable_pks = DialogVariable.objects.filter(query).order_by('date_set').values_list('pk', flat=True)

                print('dialog_variable_timeline 1.1.3 %s' % len(variable_pks))

                index = 0

                for variable_pk in variable_pks: # in DialogVariable.objects.order_by('date_set'):
                    if (index % 500) == 0:
                        print('dialog_variable_timeline: %s / %s -- %s' % (index, len(variable_pks), timezone.now().isoformat()))

                    index += 1

                    variable = DialogVariable.objects.get(pk=variable_pk)

                    sender = variable.current_sender()

                    hash_obj = hashlib.sha256()
                    hash_obj.update(sender.encode('utf-8'))

                    hash_lookup = hash_obj.hexdigest()

                    if sender in source_names:
                        row = []

                        row.append(fetch_export_identifier(variable.current_sender()))
                        row.append(variable.dialog_key)
                        row.append(variable.date_set.astimezone(here_tz).isoformat())
                        row.append(variable.key)
                        row.append(variable.value)

                        writer.writerow(row)

                    if variable.lookup_hash is None:
                        variable.lookup_hash = hash_lookup
                        variable.save()

        return filename

    return None

def simple_data_export_fields(data_type):
    if data_type in ('simple_messaging.conversation_transcripts', 'users_scheduling.link_clicks',):
        return [
            'Django Dialog Engine: Active Dialog',
        ]

    return []

def simple_data_export_field_values(data_type, context, extra_fields): # pylint: disable=invalid-name
    values = {}

    if data_type in ('simple_messaging.conversation_transcripts', 'users_scheduling.link_clicks',): # pylint: disable=too-many-nested-blocks
        for extra_field in extra_fields:
            if extra_field == 'Django Dialog Engine: Active Dialog':
                participant = context.get('raw_recipient', None)

                if participant is None:
                    participant = context.get('raw_sender', None)

                if participant is None:
                    participant = context.get('participant', None)

                if participant is not None:
                    when = context.get('datetime', None)

                    query = Q(started__lte=when) & (Q(finished=None) | Q(finished__gte=when))

                    dialogs = []

                    for session in DialogSession.objects.filter(query):
                        if session.current_destination() == participant:
                            dialogs.append(session.dialog.script.identifier)

                    values[extra_field] = ', '.join(dialogs)

    return values
