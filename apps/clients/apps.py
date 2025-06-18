# apps/clients/apps.py

from django.apps import AppConfig


class ClientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.clients'
    verbose_name = 'Clients' # A human-readable name for the app
