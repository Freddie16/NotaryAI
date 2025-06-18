# apps/dashboard/urls.py

from django.urls import path
from . import views

# Define app_name for URL namespacing (optional but recommended)
app_name = 'dashboard'

urlpatterns = [
    # Define URL patterns for the dashboard app here
    # Example: A root dashboard view
    path('', views.dashboard_view, name='dashboard'),
    # Add other dashboard-related URLs as needed
]
