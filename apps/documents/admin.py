# apps/documents/admin.py

from django.contrib import admin
from .models import Document

# Customize the admin interface for the Document model
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'uploaded_by', 'upload_date', 'file_type', 'file_size', 'status')
    list_filter = ('status', 'upload_date', 'file_type')
    search_fields = ('name', 'uploaded_by__username') # Allow searching by document name or uploader username
    readonly_fields = ('upload_date', 'file_size', 'file_type', 'summary', 'segmentation_result') # Fields that should not be editable in admin

    # Add actions to trigger AI processing from the admin list view
    actions = ['summarize_selected_documents', 'segment_selected_documents']

    def summarize_selected_documents(self, request, queryset):
        from .utils import summarize_document
        for document in queryset:
            # You might want to run this in a background task for large documents
            # For simplicity here, we run it directly
            if document.file:
                 try:
                     document.status = 'processing'
                     document.save()
                     summary = summarize_document(document.file.path)
                     if summary:
                         document.summary = summary
                         document.status = 'processed'
                         document.save()
                         self.message_user(request, f"Successfully summarized document: {document.name}")
                     else:
                         document.status = 'error'
                         document.save()
                         self.message_user(request, f"Failed to summarize document: {document.name}", level='ERROR')
                 except Exception as e:
                     document.status = 'error'
                     document.save()
                     self.message_user(request, f"Error processing document {document.name}: {e}", level='ERROR')

    summarize_selected_documents.short_description = "Summarize selected documents using AI"

    def segment_selected_documents(self, request, queryset):
        from .utils import segment_document
        for document in queryset:
            # Similar to summarization, consider background tasks
            if document.file:
                 try:
                     document.status = 'processing'
                     document.save()
                     segmentation_result = segment_document(document.file.path)
                     if segmentation_result:
                         document.segmentation_result = segmentation_result
                         document.status = 'processed'
                         document.save()
                         self.message_user(request, f"Successfully segmented document: {document.name}")
                     else:
                         document.status = 'error'
                         document.save()
                         self.message_user(request, f"Failed to segment document: {document.name}", level='ERROR')
                 except Exception as e:
                     document.status = 'error'
                     document.save()
                     self.message_user(request, f"Error processing document {document.name}: {e}", level='ERROR')

    segment_selected_documents.short_description = "Segment selected documents using AI"


# Register the Document model with the custom admin class
admin.site.register(Document, DocumentAdmin)
