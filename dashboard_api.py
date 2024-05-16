# pylint: disable=line-too-long, no-member

import statistics

from django.utils import timezone

from .models import DialogSession

def dashboard_signals():
    return [{
        'name': 'Dialog Sessions',
        'refresh_interval': 300,
        'configuration': {
            'widget_columns': 6
        }
    }]

def dashboard_template(signal_name):
    if signal_name == 'Dialog Sessions':
        return 'simple_dashboard_widget_dialog_sessions.html'

    return None

def update_dashboard_signal_value(signal_name):
    if signal_name == 'Dialog Sessions':
        open_sessions = DialogSession.objects.filter(finished=None)
        closed_sessions = DialogSession.objects.exclude(finished=None)

        value = {
            'total_sessions': DialogSession.objects.all().count(),
            'open_sessions': open_sessions.count(),
            'closed_sessions': closed_sessions.count(),
        }

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

        if len(open_durations) > 0:
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

    return None
