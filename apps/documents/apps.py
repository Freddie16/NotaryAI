# apps/documents/apps.py

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # The 'name' attribute must match the dotted path to this app
    name = 'apps.documents'
    verbose_name = 'Documents' # A human-readable name for the app
