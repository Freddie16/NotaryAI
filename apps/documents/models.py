# apps/documents/models.py

from django.db import models
from django.conf import settings # To link to the custom user model
import os # To handle file paths

# Import models from other apps (will be created later)
# Use strings for ForeignKey relationships if the models are in other apps
# to avoid circular imports.
# from apps.clients.models import Client # Example
# from apps.workflows.models import Matter # Example

class Document(models.Model):
    """
    Model to represent a document uploaded by a user.
    """
    # Link to the user who uploaded the document
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # The actual document file
    # upload_to specifies a subdirectory within MEDIA_ROOT
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    related_name='documents'

    # Document metadata
    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100) # e.g., 'application/pdf', 'image/jpeg'
    upload_date = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField() # Size in bytes

    # Link to other related models (assuming they exist in other apps)
    # Use null=True, blank=True as these might not be linked immediately on upload
    client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True) # Uncommented
    matter = models.ForeignKey('workflows.Matter', on_delete=models.SET_NULL, null=True, blank=True) # Uncommented

    # Fields for AI processing results
    summary = models.TextField(blank=True, null=True)
    segmentation_result = models.TextField(blank=True, null=True) # Store segmentation results

    # Document status (e.g., pending, processed, archived)
    STATUS_CHOICES = (
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('archived', 'Archived'),
        ('error', 'Error'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')

    # Fields for document editing/QES (can be added later)
    # e.g., edited_file = models.FileField(upload_to='edited_documents/', blank=True, null=True)
    # qes_status = models.CharField(max_length=20, blank=True, null=True)


    def __str__(self):
        # String representation of the document
        return self.name

    def save(self, *args, **kwargs):
        # Automatically set file_size and file_type on save if not set
        if not self.file_size and self.file:
            self.file_size = self.file.size
        if not self.file_type and self.file:
            import mimetypes
            self.file_type = mimetypes.guess_type(self.file.name)[0] or 'application/octet-stream'

        # Set the name if it's not provided (use the filename)
        if not self.name and self.file:
             self.name = os.path.basename(self.file.name)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the actual file when the Document object is deleted
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

    class Meta:
        # Order documents by upload date by default
        ordering = ['-upload_date']

