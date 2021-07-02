from django.contrib import admin

# Register your models here.

from .models import DialogSession, DialogVariable

@admin.register(DialogSession)
class DialogSessionAdmin(admin.ModelAdmin):
    list_display = ('destination', 'dialog', 'started', 'last_updated', 'finished')
    search_fields = ('destination',)
    list_filter = ('started', 'last_updated', 'finished',)

@admin.register(DialogVariable)
class DialogVariableAdmin(admin.ModelAdmin):
    list_display = ('sender', 'dialog_key', 'date_set', 'key', 'value_truncated',)
    search_fields = ('sender', 'dialog_key', 'key', 'value',)
    list_filter = ('date_set', 'dialog_key', 'key', 'sender')
