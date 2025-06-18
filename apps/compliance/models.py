# apps/compliance/models.py

from django.db import models
from django.conf import settings

# Import models from other apps using string references
# These models (Client, Matter) are assumed to exist in other apps (clients, workflows)
# You will need to create these apps and models for these ForeignKeys to work.
# from apps.clients.models import Client # Example import
# from apps.workflows.models import Matter # Example import

class ComplianceWorkflowTemplate(models.Model):
    """
    Defines a template for a compliance workflow (e.g., AML Check for Individual).
    Contains a set of standard questions and required checks.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ComplianceQuestion(models.Model):
    """
    Defines a standard question used in compliance checks.
    """
    question_text = models.TextField()
    # Type of answer expected (e.g., text, boolean, choice)
    ANSWER_TYPE_CHOICES = (
        ('text', 'Text'),
        ('boolean', 'Yes/No'),
        ('choice', 'Multiple Choice'),
        ('date', 'Date'),
        ('file', 'File Upload'),
    )
    answer_type = models.CharField(max_length=20, choices=ANSWER_TYPE_CHOICES, default='text')
    # For 'choice' type, store options (e.g., JSON or a simple comma-separated string)
    choice_options = models.TextField(blank=True, null=True, help_text="Comma-separated options for 'choice' type")
    is_required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text[:50] + '...' if len(self.question_text) > 50 else self.question_text

class ComplianceWorkflowTemplateQuestion(models.Model):
    """
    Links ComplianceWorkflowTemplate to ComplianceQuestion and defines the order.
    """
    template = models.ForeignKey(ComplianceWorkflowTemplate, on_delete=models.CASCADE)
    question = models.ForeignKey(ComplianceQuestion, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('template', 'question') # A question should appear only once per template

    def __str__(self):
        return f"{self.template.name} - {self.question.question_text[:30]}..."


class ComplianceCheck(models.Model):
    """
    Represents a specific instance of a compliance check for a client or matter.
    """
    # Link to the client and/or matter this check relates to
    # Use string references as Client/Matter models are in other apps
    client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True)
    matter = models.ForeignKey('workflows.Matter', on_delete=models.SET_NULL, null=True, blank=True)

    # Link to the template used for this check (optional, can be a custom check)
    template = models.ForeignKey(ComplianceWorkflowTemplate, on_delete=models.SET_NULL, null=True, blank=True)

    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('requires_review', 'Requires Review'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('error', 'Error'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Fields to store results/references from third-party checks
    credas_check_id = models.CharField(max_length=100, blank=True, null=True, help_text="Reference ID from Credas check")
    credas_result = models.TextField(blank=True, null=True) # Store relevant Credas result data

    peps_sanctions_check_id = models.CharField(max_length=100, blank=True, null=True, help_text="Reference ID from PEPs/Sanctions check")
    peps_sanctions_result = models.TextField(blank=True, null=True) # Store relevant PEPs/Sanctions result data

    # Add fields for other third-party checks as needed

    notes = models.TextField(blank=True, null=True, help_text="Internal notes about the check")

    def __str__(self):
        identifier = f"Check #{self.pk}"
        if self.client:
            identifier += f" for Client: {self.client}" # Assumes Client model has a __str__
        if self.matter:
             identifier += f" for Matter: {self.matter}" # Assumes Matter model has a __str__
        if self.template:
            identifier += f" ({self.template.name})"
        return identifier

    class Meta:
        ordering = ['-initiated_at']


class ComplianceAnswer(models.Model):
    """
    Stores the answer to a specific ComplianceQuestion for a ComplianceCheck.
    """
    compliance_check = models.ForeignKey(ComplianceCheck, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(ComplianceQuestion, on_delete=models.CASCADE)

    # Fields to store different types of answers
    answer_text = models.TextField(blank=True, null=True)
    answer_boolean = models.BooleanField(blank=True, null=True)
    answer_choice = models.CharField(max_length=255, blank=True, null=True) # Store the selected choice
    answer_date = models.DateField(blank=True, null=True)
    answer_file = models.FileField(upload_to='compliance_files/%Y/%m/%d/', blank=True, null=True)

    answered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('compliance_check', 'question') # Only one answer per question per check
        ordering = ['question__id'] # Order by question ID for consistency

    def __str__(self):
        return f"Answer for Check {self.compliance_check.pk} - {self.question.question_text[:30]}..."

