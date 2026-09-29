# pylint: disable=line-too-long, wrong-import-position

import sys

if sys.version_info[0] > 2:
    from django.urls import re_path as url # pylint: disable=no-name-in-module
else:
    from django.conf.urls import url

from .views import dashboard_dialog_alerts

urlpatterns = [
    url(r'^dashboard/alerts$', dashboard_dialog_alerts, name='dashboard_dialog_alerts'),
]
