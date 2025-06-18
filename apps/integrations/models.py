# apps/integrations/models.py

from django.db import models
from django.conf import settings

class Integration(models.Model):
    """
    Model to store configurations for external service integrations.
    """
    SERVICE_CHOICES = (
        ('credas', 'Credas (KYC/AML)'),
        ('peps_sanctions', 'PEPs and Sanctions Check'),
        ('zoom', 'Zoom (Video Conferencing)'),
        ('gmail', 'Gmail (Email)'), # Changed from 'outlook' to 'gmail'
        # Add other services here
    )

    service_name = models.CharField(max_length=50, choices=SERVICE_CHOICES, unique=True)
    is_enabled = models.BooleanField(default=False)
    api_key = models.CharField(max_length=255, blank=True, null=True) # For API Key based auth
    api_secret = models.CharField(max_length=255, blank=True, null=True) # For API Secret based auth

    # --- Fields for OAuth 2.0 (Used by Google, potentially Zoom, etc.) ---
    # Renamed fields to be more generic or specific to Google
    # If you need to support multiple OAuth services per Integration instance,
    # you might need separate models or more specific field names.
    # For now, assuming these are primarily for Google/Gmail.
    google_access_token = models.TextField(blank=True, null=True)
    google_refresh_token = models.TextField(blank=True, null=True) # Important for long-term access
    google_token_expires_at = models.DateTimeField(blank=True, null=True)
    # Store the scope(s) granted by the user
    google_token_scope = models.TextField(blank=True, null=True)


    # Other configuration fields specific to a service can be added here
    # e.g., credas_webhook_secret = models.CharField(...)

    # Link to the user who configured this integration (optional)
    # configured_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.get_service_name_display()} Integration ({'Enabled' if self.is_enabled else 'Disabled'})"

    class Meta:
        verbose_name = "Integration"
        verbose_name_plural = "Integrations"


class IntegrationLog(models.Model):
    """
    Model to log events related to integrations (errors, successes, webhook calls).
    """
    LEVEL_CHOICES = (
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('DEBUG', 'Debug'),
    )

    integration = models.ForeignKey(Integration, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Optional: Link to a specific object related to the log entry (e.g., a ComplianceCheck)
    related_object_type = models.CharField(max_length=100, blank=True, null=True) # e.g., 'ComplianceCheck', 'Matter'
    related_object_id = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.integration.service_name} - {self.level}: {self.message}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Integration Log"
        verbose_name_plural = "Integration Logs"

