# apps/documents/urls.py

from django.urls import path
from . import views

# Define the app namespace
app_name = 'documents' # <-- Added app namespace for URL namespacing

urlpatterns = [
    # URL pattern for the document list page
    path('', views.document_list_view, name='document_list'),

    # URL pattern for handling general document uploads (can still be used)
    path('upload/', views.document_upload_view, name='document_upload'),

    # NEW URL pattern for uploading a document specifically linked to a matter
    # This pattern includes the matter's primary key in the URL
    # Note: The path is relative to the app's root, so '/documents/matters/...'
    path('matters/<int:matter_pk>/upload/', views.document_upload_for_matter_view, name='document_upload_for_matter'), # <-- Corrected URL pattern

    # URL pattern for viewing a specific document's details (using its primary key)
    path('<int:pk>/', views.document_detail_view, name='document_detail'),

    # URL pattern for deleting a specific document
    path('<int:pk>/delete/', views.document_delete_view, name='document_delete'),

    # URL pattern to trigger AI summarization for a document
    path('<int:pk>/summarize/', views.document_summarize_view, name='document_summarize'),

    # URL pattern to trigger AI segmentation for a document
    path('<int:pk>/segment/', views.document_segment_view, name='document_segment'),

    # Add URL patterns for other document operations here
    path('<int:pk>/edit/', views.document_edit_view, name='document_edit'),
    path('<int:pk>/convert/', views.document_convert_view, name='document_convert'),
    path('<int:pk>/qes/', views.document_apply_qes_view, name='document_apply_qes'),
    path('<int:pk>/download/', views.document_download_view, name='document_download'),
]
