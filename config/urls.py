# config/urls.py
# Project-level URL configuration for notaryai.

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView # Import RedirectView

# Import the dashboard view
from apps.dashboard.views import dashboard_view

urlpatterns = [
    # Admin site URL
    path('admin/', admin.site.urls),

    # Include URL patterns from your local apps
    path('accounts/', include('apps.accounts.urls')),
    path('documents/', include('apps.documents.urls')),
    path('compliance/', include('apps.compliance.urls')),
    path('clients/', include('apps.clients.urls')),

    # Include the workflows app URLs and specify the namespace
    # This tells Django to register the URLs from apps.workflows.urls
    # under the 'workflows' namespace.
    path('workflows/', include('apps.workflows.urls', namespace='workflows')),

    path('integrations/', include('apps.integrations.urls')),

    # Dashboard URL
    # Assuming the dashboard view is at the root of the dashboard app
    path('dashboard/', dashboard_view, name='dashboard'), # <-- Added Dashboard URL

    # Include Django Allauth URLs if using (uncomment if allauth is in INSTALLED_APPS)
    # path('accounts/', include('allauth.urls')), # Allauth provides its own account URLs

    # Define a root URL pattern
    # Redirect the root URL to the login page or another starting page
    # Example: Redirect the root URL to the dashboard (requires login)
    path('', RedirectView.as_view(url='/dashboard/', permanent=True), name='home'), # Redirect root to dashboard

]

# Serve static and media files during development
# In production, a web server (like Nginx or Apache) should handle serving static/media files.
if settings.DEBUG:
    # Serve static files from STATIC_ROOT
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Serve media files from MEDIA_ROOT
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

