# apps/workflows/admin.py

from django.contrib import admin
from .models import (
    Matter,
    WorkflowTemplate,
    WorkflowStepTemplate,
    Workflow,
    WorkflowStep
)

# Inline admin for WorkflowStepTemplate within a WorkflowTemplate
class WorkflowStepTemplateInline(admin.TabularInline):
    model = WorkflowStepTemplate
    extra = 1 # Allow adding one extra step template form
    fields = ('name', 'description', 'order', 'is_required')

@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    inlines = [WorkflowStepTemplateInline] # Include step templates inline

@admin.register(WorkflowStepTemplate)
class WorkflowStepTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'order', 'is_required')
    list_filter = ('template', 'is_required')
    search_fields = ('name', 'description', 'template__name')

# Inline admin for WorkflowStep within a Workflow
class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 0 # Don't show extra blank forms by default
    fields = ('step_template', 'name', 'description', 'order', 'status', 'assigned_to', 'due_date', 'completed_at', 'notes')
    readonly_fields = ('completed_at',) # Completed date is set when status is changed to completed

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('matter', 'template', 'status', 'initiated_at', 'completed_at')
    list_filter = ('status', 'template', 'initiated_at')
    search_fields = ('matter__protocol_number', 'template__name') # Assuming Matter has protocol_number
    readonly_fields = ('initiated_at', 'completed_at', 'ai_generated_steps')
    inlines = [WorkflowStepInline] # Include workflow steps inline

    # Optional: Add action to trigger AI step generation
    actions = ['generate_ai_steps']

    def generate_ai_steps(self, request, queryset):
        from .utils import generate_workflow_steps_ai
        for workflow in queryset:
            if workflow.matter:
                try:
                    # Call the utility function (consider background task)
                    steps_list = generate_workflow_steps_ai(workflow.matter.title, workflow.matter.description)
                    if steps_list:
                        # Store the AI-generated steps as JSON
                        workflow.ai_generated_steps = steps_list
                        workflow.save()
                        self.message_user(request, f"AI steps generated for Workflow for Matter {workflow.matter.protocol_number}.")
                        # You might want another action or process to convert these into actual WorkflowStep objects
                    else:
                         self.message_user(request, f"AI failed to generate steps for Workflow for Matter {workflow.matter.protocol_number}.", level='WARNING')
                except Exception as e:
                     self.message_user(request, f"Error triggering AI steps for Workflow for Matter {workflow.matter.protocol_number}: {e}", level='ERROR')
            else:
                self.message_user(request, f"Workflow {workflow.pk} is not linked to a Matter. Cannot generate AI steps.", level='WARNING')
    generate_ai_steps.short_description = "Generate AI steps for selected workflows"


@admin.register(Matter)
class MatterAdmin(admin.ModelAdmin):
    list_display = ('protocol_number', 'title', 'status', 'start_date', 'due_date', 'created_by')
    list_filter = ('status', 'start_date', 'due_date', 'created_by')
    search_fields = ('protocol_number', 'title', 'description', 'clients__first_name', 'clients__last_name', 'clients__business_name') # Search by client names too
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('clients', 'assigned_users') # Use a better widget for ManyToManyFields

    # Automatically set the created_by field
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# WorkflowStep is typically managed via the Workflow inline,
# but you can register it separately if needed.
@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ('name', 'workflow', 'order', 'status', 'assigned_to', 'due_date', 'completed_at')
    list_filter = ('status', 'assigned_to', 'due_date')
    search_fields = ('name', 'description', 'workflow__matter__protocol_number')
    readonly_fields = ('completed_at',)

