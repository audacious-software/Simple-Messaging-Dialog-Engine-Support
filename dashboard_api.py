# pylint: disable=line-too-long, no-member, len-as-condition, too-many-locals, too-many-statements, import-outside-toplevel

import datetime
import statistics

import pytz

from django.conf import settings
from django.utils import timezone

from .models import DialogSession

def dashboard_signals():
    return [{
        'name': 'Dialog Sessions',
        'refresh_interval': 300,
        'configuration': {
            'widget_columns': 6,
            'active': True,
        },
    }, {
        'name': 'Daily Dialog Sessions',
        'refresh_interval': 900,
        'configuration': {
            'widget_columns': 6,
            'active': True,
        },
    }]

def dashboard_template(signal_name):
    if signal_name == 'Dialog Sessions':
        return 'dashboard/simple_dashboard_widget_dialog_sessions.html'

    if signal_name == 'Daily Dialog Sessions':
        return 'dashboard/simple_dashboard_widget_daily_sessions.html'

    return None

def update_dashboard_signal_value(signal_name): # pylint: disable=too-many-branches
    try:
        from simple_dashboard.models import DashboardSignal

        if signal_name == 'Dialog Sessions':
            open_sessions = DialogSession.objects.filter(finished=None)
            closed_sessions = DialogSession.objects.exclude(finished=None)

            value = {
                'total_sessions': DialogSession.objects.all().count(),
                'open_sessions': open_sessions.count(),
                'closed_sessions': closed_sessions.count(),
            }

            value['display_value'] = '%s total sessions, %s open sessions, %s closed sessions' % (value['total_sessions'], value['open_sessions'], value['closed_sessions'])

            now = timezone.now()

            open_durations = []
            open_max_session = None
            open_max_duration = 0

            for session in open_sessions:
                duration = (now - session.started).total_seconds()

                open_durations.append(duration)

                if open_max_session is None or duration > open_max_duration:
                    open_max_duration = duration
                    open_max_session = session

            if len(open_durations) > 1:
                value['open_session_mean_duration'] = statistics.mean(open_durations)
                value['open_session_stdev_duration'] = statistics.stdev(open_durations)
                value['open_session_max_duration'] = open_max_duration
                value['open_session_max_session'] = '%s (%s)' % (open_max_session.dialog, open_max_session.started.date())

            closed_durations = []
            closed_max_session = None
            closed_max_duration = 0

            for session in closed_sessions:
                duration = (session.finished - session.started).total_seconds()

                closed_durations.append(duration)

                if closed_max_session is None or duration > closed_max_duration:
                    closed_max_duration = duration
                    closed_max_session = session

            if len(closed_durations) > 0:
                value['closed_session_mean_duration'] = statistics.mean(closed_durations)
                value['closed_session_stdev_duration'] = statistics.stdev(closed_durations)
                value['closed_session_max_duration'] = closed_max_duration
                value['closed_session_max_session'] = '%s (%s)' % (closed_max_session.dialog, closed_max_session.started.date())

            return value

        if signal_name == 'Daily Dialog Sessions':
            start_date = None

            first_started = DialogSession.objects.all().order_by('started').first()

            if first_started is not None:
                start_date = first_started.started

            here_tz = pytz.timezone(settings.TIME_ZONE)

            today = timezone.now().astimezone(here_tz).date()

            if start_date is None:
                start_date = timezone.now() - datetime.timedelta(days=7)

            start_date = start_date.astimezone(here_tz).date()

            signal = DashboardSignal.objects.filter(name='Daily Dialog Sessions').first()

            if signal is not None:
                window_size = signal.configuration.get('window_size', 60)

                window_start = today - datetime.timedelta(days=window_size)

                start_date = max(start_date, window_start)

            session_dates = []

            while start_date <= today:
                day_start = datetime.time(0, 0, 0, 0)

                lookup_start = here_tz.localize(datetime.datetime.combine(start_date, day_start))

                day_end = datetime.time(23, 59, 59, 999999)

                lookup_end = here_tz.localize(datetime.datetime.combine(start_date, day_end))

                day_log = {
                    'date': start_date.isoformat(),
                    'sessions_started': DialogSession.objects.filter(started__gte=lookup_start, started__lte=lookup_end).count(),
                    'sessions_finished': DialogSession.objects.filter(finished__gte=lookup_start, finished__lte=lookup_end).count(),
                }

                session_dates.append(day_log)

                start_date += datetime.timedelta(days=1)

            return session_dates
    except ImportError:
        pass

    return None
