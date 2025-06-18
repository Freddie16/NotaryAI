# apps/documents/forms.py

from django import forms
from .models import Document

class DocumentUploadForm(forms.ModelForm):
    """
    Form for uploading a new document.
    """
    class Meta:
        model = Document
        # Fields for the user to fill in.
        # 'uploaded_by', 'upload_date', 'file_size', 'file_type', 'status'
        # will be set automatically or in the view.
        fields = ['file', 'name'] # Allow user to optionally name the document

        # You can add widgets for better control over form elements
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional Document Name'}),
        }

    # You can add custom validation if needed
    def clean_file(self):
        file = self.cleaned_data.get('file')
    #     # Example: Check file size or type
        if file.size > 10 * 1024 * 1024: # 10 MB limit
            raise forms.ValidationError("File size cannot exceed 10 MB.")
        return file

# Form for editing document metadata (optional)
class DocumentEditForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'client', 'matter'] # Example fields for editing links

