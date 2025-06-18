# apps/dashboard/apps.py

from django.apps import AppConfig

class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # The 'name' attribute must match the dotted path to this app
    name = 'apps.dashboard'
    verbose_name = 'Dashboard' # A human-readable name for the app

