# apps/compliance/apps.py

from django.apps import AppConfig


class ComplianceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # The 'name' attribute must match the dotted path to this app
    name = 'apps.compliance'
    verbose_name = 'Compliance' # A human-readable name for the app
