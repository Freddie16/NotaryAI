# apps/workflows/urls.py

from django.urls import path
from . import views

# Define the application namespace.
# This MUST be present if you are using a namespace in include() in your project's urls.py.
app_name = 'workflows'

urlpatterns = [
    # URL pattern for the list of matters
    path('matters/', views.matter_list_view, name='matter_list'),

    # URL pattern for creating a new matter
    path('matters/create/', views.matter_create_view, name='matter_create'),

    # URL pattern for viewing details of a specific matter
    path('matters/<int:pk>/', views.matter_detail_view, name='matter_detail'),

    # URL pattern for updating a specific matter
    path('matters/<int:pk>/edit/', views.matter_update_view, name='matter_update'),

    # URL pattern for deleting a specific matter
    path('matters/<int:pk>/delete/', views.matter_delete_view, name='matter_delete'),

    # URL pattern for viewing and managing the workflow for a specific matter
    # Note: This URL uses the matter's primary key to find its related workflow
    path('matters/<int:matter_pk>/workflow/', views.workflow_detail_view, name='workflow_detail'),

    # URL pattern for creating a workflow for a specific matter
    path('matters/<int:matter_pk>/workflow/create/', views.workflow_create_view, name='workflow_create'),

    # URL pattern to trigger AI workflow step generation for a specific workflow
    path('workflows/<int:workflow_pk>/trigger-ai-steps/', views.workflow_trigger_ai_steps_view, name='workflow_trigger_ai_steps'),


    # Add URL patterns for Workflow Templates if needed
    # path('templates/', views.workflow_template_list_view, name='workflow_template_list'),
    # path('templates/<int:pk>/', views.workflow_template_detail_view, name='workflow_template_detail'),
]
