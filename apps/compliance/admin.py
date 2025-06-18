# apps/compliance/admin.py

from django.contrib import admin
from .models import (
    ComplianceWorkflowTemplate,
    ComplianceQuestion,
    ComplianceWorkflowTemplateQuestion,
    ComplianceCheck,
    ComplianceAnswer
)

# Inline admin for questions within a workflow template
class ComplianceWorkflowTemplateQuestionInline(admin.TabularInline):
    model = ComplianceWorkflowTemplateQuestion
    extra = 1  # Allow adding one extra question link form

@admin.register(ComplianceWorkflowTemplate)
class ComplianceWorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    inlines = [ComplianceWorkflowTemplateQuestionInline]  # Include questions inline

@admin.register(ComplianceQuestion)
class ComplianceQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'answer_type', 'is_required', 'created_at')
    list_filter = ('answer_type', 'is_required')
    search_fields = ('question_text',)

# Inline admin for answers within a compliance check
class ComplianceAnswerInline(admin.TabularInline):
    model = ComplianceAnswer
    extra = 0  # Don't show extra blank forms by default
    readonly_fields = ('answered_by', 'answered_at')  # Answers are typically recorded via the front-end

@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ('pk', 'client', 'matter', 'template', 'status', 'initiated_at', 'completed_at', 'initiated_by')
    list_filter = ('status', 'template', 'initiated_at')
    search_fields = ('client__name', 'matter__protocol_number', 'notes')  # Assuming client has 'name' and matter has 'protocol_number'
    readonly_fields = ('initiated_at', 'completed_at', 'initiated_by')
    inlines = [ComplianceAnswerInline]  # Show answers inline

    # Optional: Add actions to trigger third-party checks from admin
    actions = ['trigger_credas_check', 'trigger_peps_sanctions_check']

    def trigger_credas_check(self, request, queryset):
        from .utils import trigger_credas_check
        for check in queryset:
            if check.client:  # Credas check usually requires client info
                try:
                    # Call the utility function (consider background task)
                    success, message, check_id = trigger_credas_check(check.client)
                    if success:
                        check.credas_check_id = check_id
                        check.status = 'in_progress'  # Or a specific status for external check
                        check.save()
                        self.message_user(request, f"Credas check initiated for Check {check.pk}. ID: {check_id}")
                    else:
                        check.status = 'error'
                        check.save()
                        self.message_user(request, f"Failed to initiate Credas check for Check {check.pk}: {message}", level='ERROR')
                except Exception as e:
                    check.status = 'error'
                    check.save()
                    self.message_user(request, f"Error triggering Credas check for Check {check.pk}: {e}", level='ERROR')
            else:
                self.message_user(request, f"Check {check.pk} is not linked to a client. Cannot trigger Credas check.", level='WARNING')
    trigger_credas_check.short_description = "Trigger Credas check for selected checks"

    def trigger_peps_sanctions_check(self, request, queryset):
        from .utils import trigger_peps_sanctions_check
        for check in queryset:
            if check.client:  # PEPs/Sanctions check usually requires client info
                try:
                    # Call the utility function (consider background task)
                    success, message, check_id = trigger_peps_sanctions_check(check.client)
                    if success:
                        check.peps_sanctions_check_id = check_id
                        check.status = 'in_progress'  # Or a specific status
                        check.save()
                        self.message_user(request, f"PEPs/Sanctions check initiated for Check {check.pk}. ID: {check_id}")
                    else:
                        check.status = 'error'
                        check.save()
                        self.message_user(request, f"Failed to initiate PEPs/Sanctions check for Check {check.pk}: {message}", level='ERROR')
                except Exception as e:
                    check.status = 'error'
                    check.save()
                    self.message_user(request, f"Error triggering PEPs/Sanctions check for Check {check.pk}: {e}", level='ERROR')
            else:
                self.message_user(request, f"Check {check.pk} is not linked to a client. Cannot trigger PEPs/Sanctions check.", level='WARNING')
    trigger_peps_sanctions_check.short_description = "Trigger PEPs/Sanctions check for selected checks"

@admin.register(ComplianceAnswer)
class ComplianceAnswerAdmin(admin.ModelAdmin):
    list_display = ('compliance_check', 'question', 'answered_by', 'answered_at')
    list_filter = ('answered_at', 'question__answer_type')
    search_fields = ('compliance_check__pk', 'question__question_text', 'answer_text')
    readonly_fields = ('answered_by', 'answered_at')
