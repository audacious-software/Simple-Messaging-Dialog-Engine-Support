# pylint: disable=line-too-long

from django.contrib import admin

from django.conf import settings

from .models import DialogSession, DialogVariable, DialogTemplateVariable

@admin.register(DialogSession)
class DialogSessionAdmin(admin.ModelAdmin):
    if hasattr(settings, 'SIMPLE_MESSAGING_SHOW_ENCRYPTED_VALUES') and settings.SIMPLE_MESSAGING_SHOW_ENCRYPTED_VALUES:
        list_display = ('current_destination', 'dialog', 'started', 'last_updated', 'finished')
    else:
        list_display = ('destination', 'dialog', 'started', 'last_updated', 'finished')

    list_filter = ('started', 'last_updated', 'finished',)

@admin.register(DialogVariable)
class DialogVariableAdmin(admin.ModelAdmin):
    if hasattr(settings, 'SIMPLE_MESSAGING_SHOW_ENCRYPTED_VALUES') and settings.SIMPLE_MESSAGING_SHOW_ENCRYPTED_VALUES:
        list_display = ('current_sender', 'dialog_key', 'date_set', 'key', 'value_truncated',)
    else:
        list_display = ('sender', 'dialog_key', 'date_set', 'key', 'value_truncated',)

    search_fields = ('dialog_key', 'key', 'value',)
    list_filter = ('date_set', 'dialog_key', 'key',)

@admin.register(DialogTemplateVariable)
class DialogTemplateVariableAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'script')
    search_fields = ('key', 'value',)
    list_filter = ('script',)
