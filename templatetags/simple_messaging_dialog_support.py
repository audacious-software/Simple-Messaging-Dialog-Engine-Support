from django import template
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

register = template.Library()

@register.filter
def split(str_value, separator):
    return str_value.split(separator)
