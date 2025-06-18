# apps/clients/forms.py

from django import forms # <-- Import the forms module
from .models import Client #, Lead # Uncomment Lead if you create that model
# Import Client model from clients app using the correct dotted path
# from apps.clients.models import Client # No need to re-import from apps.clients

# Import FormHelper and Submit for crispy forms if you are using them directly in the form class
# from crispy_forms.helper import FormHelper # Uncomment if needed
# from crispy_forms.layout import Submit # Uncomment if needed


class ClientForm(forms.ModelForm):
    """
    Form for creating or updating a Client.
    """
    class Meta:
        model = Client
        # Exclude fields that are set automatically or via AI
        exclude = ['created_by', 'created_at', 'updated_at', 'segmentation_tags']

        widgets = {
            'client_type': forms.Select(attrs={'class': 'form-select'}), # Use Bootstrap select styling
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), # HTML5 date input
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    # Add custom validation if needed
    # def clean(self):
    #     cleaned_data = super().clean()
    #     client_type = cleaned_data.get('client_type')
    #     first_name = cleaned_data.get('first_name')
    #     last_name = cleaned_data.get('last_name')
    #     business_name = cleaned_data.get('business_name')

    #     if client_type == 'individual' and not (first_name and last_name):
    #         raise forms.ValidationError("First name and last name are required for individual clients.")
    #     if client_type == 'business' and not business_name:
    #         raise forms.ValidationError("Business name is required for business clients.")

    #     return cleaned_data

# If you create a Lead model, create a form for it:
# class LeadForm(forms.ModelForm):
#     class Meta:
#         model = Lead
#         exclude = ['created_at', 'updated_at']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control'}),
#             'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
#             'source': forms.TextInput(attrs={'class': 'form-control'}),
#             'status': forms.Select(attrs={'class': 'form-select'}),
#             'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
#             'assigned_to': forms.Select(attrs={'class': 'form-select'}),
#         }

