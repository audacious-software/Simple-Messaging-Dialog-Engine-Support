# pylint: disable=no-member, line-too-long

import importlib

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import reverse

from .models import DialogAlert

@staff_member_required
def dashboard_dialog_alerts(request):
    context = {}

    offset = int(request.GET.get('offset', '0'))
    limit = int(request.GET.get('limit', '25'))

    alerts = DialogAlert.objects.all().order_by('-last_updated')[offset:limit]

    total = len(alerts)

    context['alerts'] = alerts
    context['start'] = offset + 1
    context['end'] = min(len(alerts), (offset + limit))
    context['total'] = total

    if (offset - limit) >= 0:
        context['previous'] = '%s?offset=%s&limit=%s' % (reverse('dashboard_dialog_alerts'), offset - limit, limit,)

    if (offset + limit) < total:
        context['next'] = '%s?offset=%s&limit=%s' % (reverse('dashboard_dialog_alerts'), offset + limit, limit,)

    context['first'] = '%s?offset=0&limit=%s' % (reverse('dashboard_dialog_alerts'), limit,)

    last = int(total / limit) * limit

    context['last'] = '%s?offset=%s&limit=%s' % (reverse('dashboard_dialog_alerts'), last, limit,)

    return render(request, 'dashboard/simple_dashboard_dashboard_alerts.html', context=context)
