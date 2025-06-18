# apps/compliance/forms.py

from django import forms
# Import all necessary models from .models
from .models import ComplianceCheck, ComplianceAnswer, ComplianceQuestion, ComplianceWorkflowTemplate
# Import Client model from clients app using the correct dotted path
from apps.clients.models import Client
# Import Matter model from workflows app using the correct dotted path if used in forms
# from apps.workflows.models import Matter # Uncomment if you use Matter in this form

# Form for initiating a new compliance check
class ComplianceCheckInitiateForm(forms.ModelForm):
    """
    Form to start a new compliance check, optionally based on a template.
    Requires linking to a client or matter (these fields will need to be
    populated dynamically or filtered based on the user/context).
    """
    # Assuming Client and Matter models exist in other apps
    # Now that Client is imported correctly, you can uncomment this field if needed
    client = forms.ModelChoiceField(queryset=Client.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-select'})) # Example - added widget
    # matter = forms.ModelChoiceField(queryset=Matter.objects.all(), required=False) # Example - Matter still needs to be imported

    # ComplianceWorkflowTemplate is now imported
    template = forms.ModelChoiceField(queryset=ComplianceWorkflowTemplate.objects.all(), required=False, help_text="Optional: Select a template to pre-populate questions.", widget=forms.Select(attrs={'class': 'form-select'})) # Added widget

    class Meta:
        model = ComplianceCheck
        # Exclude fields that will be set automatically or via answers
        # Include 'client' if you uncommented the field above
        fields = ['client', 'template', 'notes'] # Add 'matter' if you uncomment that field

        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}), # Added widget
        }

    # Add validation to ensure either client or matter is provided (if applicable)
    # def clean(self):
    #     cleaned_data = super().clean()
    #     client = cleaned_data.get('client')
    #     matter = cleaned_data.get('matter')
    #     if not client and not matter:
    #         raise forms.ValidationError("A compliance check must be linked to either a client or a matter.")
    #     return cleaned_data


# Dynamic formset for answering compliance questions
# This is more complex and often built dynamically in the view or using formsets.
# Here's a basic idea for a single answer form:

class ComplianceAnswerForm(forms.ModelForm):
    """
    Form for providing an answer to a single compliance question.
    This form would typically be used within a formset or dynamically generated.
    """
    class Meta:
        model = ComplianceAnswer
        # Fields to capture the answer based on question type
        fields = ['answer_text', 'answer_boolean', 'answer_choice', 'answer_date', 'answer_file']
        # Exclude 'compliance_check', 'question', 'answered_by', 'answered_at'
        # as these will be set in the view.

        widgets = {
            'answer_text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), # Added widget
            'answer_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), # HTML5 date input, Added widget
            'answer_file': forms.FileInput(attrs={'class': 'form-control'}), # Added widget
        }

    # You would typically customize this form based on the question's answer_type
    # in the view or using a formset factory.
    # Example: If question.answer_type is 'boolean', only show answer_boolean field.
    # This is often handled by rendering the form fields conditionally in the template
    # or by dynamically creating form classes/formsets in the view.

# Example Formset Factory (requires django.forms.formsets)
# from django.forms import formset_factory
# ComplianceAnswerFormSet = formset_factory(ComplianceAnswerForm, extra=0) # extra=0 means no blank forms by default
