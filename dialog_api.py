# pylint: disable=no-member, line-too-long
from django.utils import timezone

from .models import DialogVariable


def store_value(sender, dialog_key, key, value):
    DialogVariable.objects.create(sender=sender, dialog_key=dialog_key, key=key, value=value, date_set=timezone.now())
