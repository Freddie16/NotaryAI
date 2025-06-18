# apps/workflows/models.py

from django.db import models
from django.conf import settings # To link to the custom user model
from django.core.exceptions import ValidationError # Import ValidationError
from django.utils.translation import gettext_lazy as _ # For translatable strings
import json # For JSONField

# Import models from other apps using string references to avoid circular imports
# from apps.clients.models import Client # Example
# from apps.documents.models import Document # Example

class Matter(models.Model):
    """
    Represents a legal matter or case managed by the notary.
    """
    # Auto-generated protocol number (can be customized)
    protocol_number = models.CharField(max_length=50, unique=True, editable=False)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Status of the matter
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    # Dates
    start_date = models.DateField()
    due_date = models.DateField(blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)

    # Link to related clients (Many-to-Many relationship)
    # Use string reference 'clients.Client' as Client model is in another app
    clients = models.ManyToManyField('clients.Client', related_name='matters', blank=True)

    # Link to documents related to this matter (Many-to-Many or ForeignKey)
    # Assuming a ForeignKey from Document to Matter in the documents app
    # documents = models.ManyToManyField('documents.Document', related_name='matters', blank=True)

    # Internal notes
    notes = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Link to the user who created this matter
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    # Link to users assigned to this matter (e.g., Notary, Solicitor)
    assigned_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='assigned_matters', blank=True)


    def __str__(self):
        return f"{self.protocol_number}: {self.title}"

    def save(self, *args, **kwargs):
        # Generate protocol number if it's a new matter
        if not self.pk:
            # Simple sequential number generation (can be made more robust)
            last_matter = Matter.objects.order_by('-pk').first()
            new_pk = (last_matter.pk if last_matter else 0) + 1
            self.protocol_number = f'MAT-{new_pk:06d}' # Format with leading zeros

        super().save(*args, **kwargs)

    class Meta:
        # Order matters by protocol number by default
        ordering = ['-protocol_number']


class WorkflowTemplate(models.Model):
    """
    Defines a reusable template for a workflow (e.g., Real Estate Purchase).
    Contains a sequence of predefined steps.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class WorkflowStepTemplate(models.Model):
    """
    Defines a single step within a WorkflowTemplate.
    """
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name='step_templates')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0) # Order of the step within the workflow
    is_required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.template.name} - Step {self.order}: {self.name}"

    class Meta:
        ordering = ['order']
        # Ensure the order is unique within a single template
        unique_together = ('template', 'order') # <-- Corrected unique_together


class Workflow(models.Model):
    """
    Represents a specific instance of a workflow applied to a Matter.
    """
    # Link to the Matter this workflow belongs to (One-to-One relationship)
    # Use OneToOneField if each matter has exactly one workflow
    matter = models.OneToOneField(Matter, on_delete=models.CASCADE, related_name='workflow')

    # Link to the template used for this workflow (optional, can be a custom workflow)
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.SET_NULL, null=True, blank=True)

    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    STATUS_CHOICES = (
        ('not_started', 'Not Started'), # Added 'not_started' status
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started') # Default to 'not_started'

    # Store AI-generated step suggestions (as JSON)
    ai_generated_steps = models.JSONField(blank=True, null=True, help_text="AI-suggested workflow steps (JSON array)")

    def __str__(self):
        return f"Workflow for Matter {self.matter.protocol_number}"

    class Meta:
        ordering = ['-initiated_at']


class WorkflowStep(models.Model):
    """
    Represents a single step within a specific Workflow instance.
    """
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps')

    # Link to the template step it originated from (optional)
    step_template = models.ForeignKey(WorkflowStepTemplate, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0) # Order within the workflow instance

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'), # Added 'skipped' status
        ('blocked', 'Blocked'), # Added 'blocked' status (e.g., waiting for another step)
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # User assigned to complete this step
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_workflow_steps')

    due_date = models.DateField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    # Internal notes for the step
    notes = models.TextField(blank=True, null=True)

    # Link to documents related to this step (Many-to-Many)
    # documents = models.ManyToManyField('documents.Document', related_name='workflow_steps', blank=True)

    def __str__(self):
        return f"Step {self.order}: {self.name} ({self.get_status_display()})"

    class Meta:
        ordering = ['order']
        # Ensure the order is unique within a single workflow instance
        unique_together = ('workflow', 'order')


