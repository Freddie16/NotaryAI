# apps/integrations/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # URL pattern for the list of integrations
    path('', views.integration_list_view, name='integration_list'),

    # URL pattern for creating a new integration
    path('create/', views.integration_create_view, name='integration_create'),

    # URL pattern for configuring a specific integration
    path('<int:pk>/config/', views.integration_config_view, name='integration_config'),

    # URL pattern for deleting a specific integration
    path('<int:pk>/delete/', views.integration_delete_view, name='integration_delete'),

    # URL pattern to test a specific integration connection
    path('<int:pk>/test/', views.integration_test_view, name='integration_test'),

    # --- Google OAuth Callback URL (Replacing Microsoft Graph) ---
    # This URL is the redirect URI registered in the Google Cloud Console.
    # It receives the authorization code after the user grants permission.
    # The name 'google_oauth_callback' should match the GOOGLE_OAUTH_REDIRECT_URI in settings.py
    path('oauth/google/callback/', views.google_oauth_callback_view, name='google_oauth_callback'),

    # --- Webhook URLs (Keeping Credas and PEPs/Sanctions) ---
    # These are typically API endpoints, often exempted from CSRF (with caution!)
    path('webhooks/credas/', views.credas_webhook_view, name='credas_webhook'),
    path('webhooks/peps-sanctions/', views.peps_sanctions_webhook_view, name='peps_sanctions_webhook'),

    # --- Mobile Camera Upload URL (Placeholder) ---
    # This URL would be used by the mobile application to upload documents.
    # path('api/mobile-upload/', views.mobile_document_upload_api, name='mobile_document_upload_api'),
]
