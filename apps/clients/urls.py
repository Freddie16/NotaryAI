# apps/clients/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # URL pattern for the client list page
    path('', views.client_list_view, name='client_list'),

    # URL pattern for creating a new client
    path('create/', views.client_create_view, name='client_create'),

    # URL pattern for viewing details of a specific client
    path('<int:pk>/', views.client_detail_view, name='client_detail'),

    # URL pattern for updating a specific client
    path('<int:pk>/edit/', views.client_update_view, name='client_update'),

    # URL pattern for deleting a specific client
    path('<int:pk>/delete/', views.client_delete_view, name='client_delete'),

    # Add URL patterns for Lead management if you create a separate Lead model
    path('leads/', views.lead_list_view, name='lead_list'),
    path('leads/create/', views.lead_create_view, name='lead_create'),
    path('leads/<int:pk>/', views.lead_detail_view, name='lead_detail'),
    path('leads/<int:pk>/convert/', views.lead_convert_to_client_view, name='lead_convert_to_client'),
]
