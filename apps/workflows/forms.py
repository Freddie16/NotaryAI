# apps/workflows/forms.py

from django import forms
from django.forms.models import inlineformset_factory # Import inlineformset_factory
from .models import Matter, Workflow, WorkflowTemplate, WorkflowStep # Import WorkflowStep
from apps.clients.models import Client # Import Client model
from django.contrib.auth import get_user_model # Import get_user_model

User = get_user_model() # Get the custom user model

# Form for creating and updating Matters
class MatterForm(forms.ModelForm):
    """
    Form for creating and updating a Matter.
    """
    # Use ModelMultipleChoiceField for the ManyToMany relationships
    # Filter the queryset if needed (e.g., only show clients/users related to the current user)
    clients = forms.ModelMultipleChoiceField(
        queryset=Client.objects.all(), # You might filter this queryset
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}), # Using SelectMultiple as requested
        required=False,
        help_text="Select clients related to this matter."
    )
    assigned_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True), # Filter for active users as requested
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}), # Using SelectMultiple as requested
        required=False,
        help_text="Select users assigned to this matter."
    )

    class Meta:
        model = Matter
        # Exclude 'protocol_number' as it's non-editable and generated automatically by the model's save method.
        # Also exclude 'created_by', 'created_at', 'updated_at' which are set automatically.
        # Re-added 'start_date' as it's a standard date field.
        fields = [
            # 'protocol_number', # <-- Removed as it's non-editable in the model
            'title',
            'description',
            'status',
            'start_date', # <-- Re-added start_date
            'due_date',
            'completion_date',
            'notes',
            'clients', # Include the clients ManyToMany field
            'assigned_users', # Include the assigned_users ManyToMany field
        ]

        # Add widgets for better styling
        widgets = {
            # 'protocol_number': forms.TextInput(attrs={'class': 'form-control'}), # <-- Removed widget
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), # Added widget for start_date
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'completion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            # Widgets for ManyToMany fields are defined above
        }

        # Add help text if needed
        help_texts = {
            'status': 'Current status of the matter.',
            'start_date': 'The date the matter was initiated.',
            'due_date': 'The target date for completion.',
            'completion_date': 'The actual date the matter was completed.',
        }

        # Add error messages if needed
        error_messages = {
            'title': {'required': 'Please provide a title for the matter.'},
            'start_date': {'required': 'Please provide a start date for the matter.'},
        }

    # Custom validation for protocol_number (kept, but note conflict with model's editable=False)
    # This clean method is relevant if you change the model to make protocol_number editable
    # and want to enforce uniqueness and required status via the form.
    def clean_protocol_number(self):
        protocol_number = self.cleaned_data.get('protocol_number')
        # If protocol_number is not included in `fields`, this method won't be called
        # unless you explicitly add it back to the form fields.
        # If you make protocol_number editable in the model, uncomment the validation below.
        # if not protocol_number:
        #     raise forms.ValidationError("Protocol number is required.")
        # if Matter.objects.filter(protocol_number=protocol_number).exclude(pk=self.instance.pk).exists():
        #     raise forms.ValidationError("A matter with this protocol number already exists.")
        return protocol_number

    # You can add other custom validation methods here if needed
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        due_date = cleaned_data.get('due_date')
        completion_date = cleaned_data.get('completion_date')

        # Example validation: Due date should not be before start date
        if start_date and due_date and due_date < start_date:
            self.add_error('due_date', "Due date cannot be before the start date.")

        # Example validation: Completion date should not be before start date or due date
        if start_date and completion_date and completion_date < start_date:
             self.add_error('completion_date', "Completion date cannot be before the start date.")
        if due_date and completion_date and completion_date < due_date:
             self.add_error('completion_date', "Completion date cannot be before the due date.")

        # If status is 'closed' or 'cancelled', completion_date might be required
        status = cleaned_data.get('status')
        if status in ['closed', 'cancelled'] and not completion_date:
             self.add_error('completion_date', f"Completion date is required when status is '{status}'.")

        return cleaned_data


# Form for creating a Workflow (linked to a Matter)
class WorkflowForm(forms.ModelForm):
    """
    Form for creating a Workflow instance for a Matter.
    Allows selecting a template.
    """
    # Use ModelChoiceField for the ForeignKey to WorkflowTemplate
    template = forms.ModelChoiceField(
        queryset=WorkflowTemplate.objects.all(),
        required=False, # Template is optional (allows for custom workflows)
        empty_label="-- Select a template --", # Optional: Add an empty choice
        widget=forms.Select(attrs={'class': 'form-select'}), # Add widget for Bootstrap styling
        help_text="Optional: Select a template to pre-populate workflow steps."
    )

    class Meta:
        model = Workflow
        # Exclude fields that will be set automatically or via steps
        # 'matter' is set in the view, 'initiated_at', 'completed_at', 'status', 'ai_generated_steps'
        # 'status' is determined by the status of its steps, so it should not be in the form.
        exclude = ['matter', 'initiated_at', 'completed_at', 'status', 'ai_generated_steps'] # Exclude status as it's derived

        # Removed status widget as status is excluded from fields
        # widgets = {
        #     'status': forms.Select(attrs={'class': 'form-select'}),
        # }

    # You can add custom validation or logic here
    # def clean(self):
    #     cleaned_data = super().clean()
    #     # Add cross-field validation if needed
    #     return cleaned_data


# Form for a single Workflow Step
class WorkflowStepForm(forms.ModelForm):
    """
    Form for a single Workflow Step.
    Used within a formset for managing steps.
    """
    class Meta:
        model = WorkflowStep
        # Define fields explicitly that should be editable in the formset.
        # Removed 'exclude' here to avoid conflict with formset_factory's 'fields'.
        fields = [
            'step_template', # Link to the template step (optional)
            'name',
            'description',
            'order',
            'status',
            'assigned_to',
            'due_date',
            'notes',
            # 'completed_at' is set automatically based on status
        ]

        widgets = {
            'step_template': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}), # Assuming assigned_to is a ForeignKey to User
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

        # Add help text if needed
        help_texts = {
            'step_template': 'Select a template step to inherit name and description.',
            'order': 'The order of this step in the workflow.',
        }

    # Custom __init__ to potentially filter assigned_to users or populate fields from template
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Example: Filter assigned_to queryset to only users assigned to the matter
        # if self.instance and self.instance.workflow and self.instance.workflow.matter:
        #     self.fields['assigned_to'].queryset = self.instance.workflow.matter.assigned_users.all()

        # Example: Populate name and description from step_template if a new step
        # if not self.instance.pk and self.initial.get('step_template'):
        #      step_template = self.initial.get('step_template')
        #      self.fields['name'].initial = step_template.name
        #      self.fields['description'].initial = step_template.description


# Formset Factory for Workflow Steps
# This is used in the workflow_detail_view to handle multiple WorkflowStep forms
WorkflowStepFormSet = inlineformset_factory(
    Workflow, # Parent model
    WorkflowStep, # Child model
    form=WorkflowStepForm, # Form to use for each step
    extra=1, # Number of empty forms to display initially
    can_delete=True, # Allow deleting steps
    # Explicitly define fields to use in the formset, overriding the form's Meta
    fields=['step_template', 'name', 'description', 'order', 'status', 'assigned_to', 'due_date', 'notes']
)
