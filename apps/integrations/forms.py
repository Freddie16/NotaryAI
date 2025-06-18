# apps/integrations/forms.py

from django import forms
from .models import Integration

class IntegrationForm(forms.ModelForm):
    """
    Form for creating and updating Integration configurations.
    """
    class Meta:
        model = Integration
        # Include fields that are manually configurable
        fields = [
            'service_name',
            'is_enabled',
            'api_key',
            'api_secret',
            # Include Google OAuth fields if you want to display them,
            # but they are typically managed via the OAuth flow, not manual input.
            # 'google_access_token',
            # 'google_refresh_token',
            # 'google_token_expires_at',
            # 'google_token_scope',
        ]
        # Exclude fields that are set automatically or via OAuth flow
        # exclude = ['google_access_token', 'google_refresh_token', 'google_token_expires_at', 'google_token_scope']


        widgets = {
            'service_name': forms.Select(attrs={'class': 'form-select'}),
            'api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'api_secret': forms.TextInput(attrs={'class': 'form-control'}),
            # Add widgets for Google OAuth fields if you include them above
            # 'google_access_token': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'readonly': 'readonly'}),
            # 'google_refresh_token': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'readonly': 'readonly'}),
            # 'google_token_expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'readonly': 'readonly'}),
            # 'google_token_scope': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    # Add custom validation or logic if needed
    # def clean(self):
    #     cleaned_data = super().clean()
    #     # Example: Require API key for certain services
    #     service_name = cleaned_data.get('service_name')
    #     is_enabled = cleaned_data.get('is_enabled')
    #     api_key = cleaned_data.get('api_key')

    #     if is_enabled and service_name in ['credas', 'peps_sanctions'] and not api_key:
    #         raise forms.ValidationError(f"API Key is required to enable the {service_name} integration.")

    #     return cleaned_data

