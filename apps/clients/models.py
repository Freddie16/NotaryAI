# apps/clients/models.py

from django.db import models
from django.conf import settings  # To link to the custom user model

# Import models from other apps using string references
from apps.documents.models import Document  # Example
from apps.compliance.models import ComplianceCheck  # Example
from apps.workflows.models import Matter  # Example

class Client(models.Model):
    """
    Represents a client (individual or business) of the notary.
    """
    # Client Type
    CLIENT_TYPE_CHOICES = (
        ('individual', 'Individual'),
        ('business', 'Business'),
    )
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPE_CHOICES, default='individual')

    # Basic Information (for individuals)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # Basic Information (for businesses)
    business_name = models.CharField(max_length=255, blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True)  # e.g., company registration number

    # Contact Information
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Client Status (e.g., lead, active, inactive, archived)
    STATUS_CHOICES = (
        ('lead', 'Lead'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')

    # Internal Notes
    notes = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Link to the user who created/manages this client
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    # AI-driven segmentation result (placeholder)
    segmentation_tags = models.JSONField(blank=True, null=True, help_text="AI-generated segmentation tags")

    def __str__(self):
        """String representation of the client."""
        if self.client_type == 'business' and self.business_name:
            return self.business_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.email:
            return self.email
        elif self.phone_number:
            return self.phone_number
        else:
            return f"Client #{self.pk}"

    class Meta:
        # Order clients by creation date by default
        ordering = ['-created_at']

# You might have a separate Lead model if the lead process is distinct
# from the client model initially, but for simplicity, we'll use the
# Client model with a 'lead' status as requested.
class Lead(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)  # e.g., Website, Referral
    status = models.CharField(max_length=20, default='new')  # e.g., new, contacted, qualified, converted
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name
