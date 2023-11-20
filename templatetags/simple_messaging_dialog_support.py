from django import template

register = template.Library()

@register.filter
def split(str_value, separator):
    return str_value.split(separator)
