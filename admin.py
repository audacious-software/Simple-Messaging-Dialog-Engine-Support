# pylint: disable=line-too-long

from django.conf import settings
from django.contrib import admin
from django.db.models import Q

from django_dialog_engine.models import DialogScript

from .models import DialogSession, DialogVariable, DialogTemplateVariable, DialogAlert, LaunchKeyword

@admin.register(DialogSession)
class DialogSessionAdmin(admin.ModelAdmin):
    if hasattr(settings, 'SIMPLE_MESSAGING_SHOW_ENCRYPTED_VALUES') and settings.SIMPLE_MESSAGING_SHOW_ENCRYPTED_VALUES:
        list_display = ('current_destination', 'dialog', 'transmission_channel', 'started', 'last_updated', 'finished')
    else:
        list_display = ('destination', 'dialog', 'transmission_channel', 'started', 'last_updated', 'finished')

    readonly_fields = ['dialog']

    list_filter = ('started', 'last_updated', 'finished', 'transmission_channel',)

    def get_search_results(self, request, queryset, search_term):
        original_query_set = queryset

        queryset, may_have_duplicates = super(DialogSessionAdmin, self).get_search_results(request, queryset, search_term,) # pylint:disable=super-with-arguments

        if search_term is None or search_term == '':
            return queryset, may_have_duplicates

        for session in original_query_set:
            if search_term in session.current_destination():
                queryset = queryset | self.model.objects.filter(destination=session.destination)

        return queryset, may_have_duplicates

@admin.register(DialogVariable)
class DialogVariableAdmin(admin.ModelAdmin):
    if hasattr(settings, 'SIMPLE_MESSAGING_SHOW_ENCRYPTED_VALUES') and settings.SIMPLE_MESSAGING_SHOW_ENCRYPTED_VALUES:
        list_display = ('current_sender', 'dialog_key', 'date_set', 'key', 'value_truncated',)
    else:
        list_display = ('sender', 'dialog_key', 'date_set', 'key', 'value_truncated',)

    search_fields = ('dialog_key', 'key', 'value',)
    list_filter = ('date_set', 'dialog_key', 'key',)

    def get_search_results(self, request, queryset, search_term):
        original_query_set = queryset

        queryset, may_have_duplicates = super(DialogVariableAdmin, self).get_search_results(request, queryset, search_term,) # pylint:disable=super-with-arguments

        if search_term is None or search_term == '':
            return queryset, may_have_duplicates

        for variable in original_query_set:
            if search_term in variable.current_sender():
                queryset = queryset | self.model.objects.filter(sender=variable.sender)

        return queryset, may_have_duplicates

@admin.register(DialogTemplateVariable)
class DialogTemplateVariableAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'script')
    search_fields = ('key', 'value',)
    list_filter = ('script',)

@admin.register(DialogAlert)
class DialogAlertAdmin(admin.ModelAdmin):
    list_display = ('current_sender', 'added', 'last_updated', 'dialog', 'message')
    search_fields = ('message', 'current_sender', 'metadata',)
    list_filter = ('added', 'last_updated',)

@admin.register(LaunchKeyword)
class LaunchKeywordAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs): # pylint: disable=arguments-differ
        form = super(LaunchKeywordAdmin, self).get_form(request, obj, **kwargs) # pylint: disable=super-with-arguments

        query = None

        for script in DialogScript.objects.all():
            if script.is_active():
                if query is None:
                    query = Q(pk=script.pk)
                else:
                    query = query | Q(pk=script.pk) # pylint: disable=unsupported-binary-operation

        form.base_fields['dialog_script'].queryset = DialogScript.objects.filter(query)

        return form

    list_display = ('keyword', 'dialog_script', 'case_sensitive', 'priority',)
    search_fields = ('keyword', 'dialog_script',)
    list_filter = ('case_sensitive',)
