# pylint: disable=line-too-long, no-member

import csv
import importlib
import io
import os
import tempfile

import pytz

from django.conf import settings

from simple_data_export.utils import fetch_export_identifier

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
    ]

def compile_data_export(data_type, data_sources, start_time=None, end_time=None, custom_parameters=None): # pylint: disable=too-many-locals, unused-argument, too-many-branches
    here_tz = pytz.timezone(settings.TIME_ZONE)

    if data_type == 'simple_messaging_dialog_support.dialog_variables':
        filename = tempfile.gettempdir() + os.path.sep + 'simple_messaging_dialog_support.dialog_variables.txt'

        with io.open(filename, 'w', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, delimiter='\t')

            variables = [
                'Destination',
                'Dialog',
                'Started',
                'Finished',
                'Cancelled',
            ]

            dialog_variables = []

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

            if len(dialog_variables) == 0: # pylint: disable=len-as-condition
                for variable in DialogVariable.objects.all().order_by('date_set'):
                    if (variable.key in dialog_variables) is False:
                        dialog_variables.append(variable.key)

            variables.extend(dialog_variables)

            writer.writerow(variables)

            for session in DialogSession.objects.exclude(finished=None).order_by('started'):
                destination = session.current_destination()

                if destination in data_sources:
                    session_variables = {
                        'Destination': fetch_export_identifier(destination),
                        'Dialog': session.dialog.key,
                        'Started': session.started.astimezone(here_tz).isoformat(),
                        'Finished': session.finished.astimezone(here_tz).isoformat(),
                        'Cancelled': False,
                    }

                    if session.dialog.finish_reason in ('user_cancelled', 'dialog_cancelled', 'timed_out',):
                        session_variables['Cancelled'] = True

                    for variable in DialogVariable.objects.filter(date_set__gte=session.started, date_set__lte=session.finished).order_by('date_set'):
                        if variable.current_sender() == destination:
                            if (variable.key in session_variables) is False:
                                session_variables[variable.key] = []

                            session_variables[variable.key].append(variable.value)

                    row = []

                    for variable in variables:
                        if variable in session_variables:
                            value = session_variables[variable]

                            if isinstance(value, list):
                                row.append('; '.join(value))
                            else:
                                row.append(value)
                        else:
                            row.append('')

                    writer.writerow(row)

        return filename

    return None
