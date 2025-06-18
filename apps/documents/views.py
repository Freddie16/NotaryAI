# apps/documents/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Import necessary modules for document download
from django.http import HttpResponse, Http404
from django.conf import settings
import os
import mimetypes
from django.core.files.storage import default_storage
from django.urls import reverse
from django.db.models import Q # Import Q for complex lookups

from .models import Document
# Import forms used in views
from .forms import DocumentUploadForm, DocumentEditForm
# Import utility functions
from .utils import summarize_document, segment_document, get_document_content
# Import custom decorators from accounts app if needed for role-based access
# from apps.accounts.utils import notary_required, admin_required
# Import the Matter model to link documents to matters
from apps.workflows.models import Matter # <-- Import Matter model


@login_required # Require user to be logged in
# @notary_required # Example: Only allow notaries to access document list
def document_list_view(request):
    """
    View to list all documents.
    Filters based on user role and optionally by matter via GET parameter.
    """
    # Base queryset - filter by the logged-in user or show all for admin
    if request.user.is_superuser or request.user.role == 'admin':
         documents = Document.objects.all()
    else:
         # Assuming users only see documents they uploaded or those linked to their matters/clients
         # This is a simplified filter; you might need more complex logic here
         documents = Document.objects.filter(uploaded_by=request.user)
         # Example with Matter/Client linkage (requires those models to be correctly linked to User)
         # from apps.clients.models import Client # Assuming Client model exists
         # from apps.workflows.models import Matter # Assuming Matter model exists
         # user_clients = Client.objects.filter(assigned_users=request.user) # Example: User is assigned to client
         # user_matters = Matter.objects.filter(assigned_users=request.user) # Example: User is assigned to matter
         # documents = Document.objects.filter(
         #     Q(uploaded_by=request.user) |
         #     Q(client__in=user_clients) |
         #     Q(matter__in=user_matters)
         # ).distinct()


    # Filter by matter if matter_pk is provided in GET parameters
    matter_pk = request.GET.get('matter')
    matter = None
    if matter_pk:
        try:
            # Get the matter to display its info
            matter = get_object_or_404(Matter, pk=matter_pk)
            # Further filter documents to only those linked to this matter
            documents = documents.filter(matter=matter)
            messages.info(request, f"Showing documents for Matter: {matter.protocol_number}")
        except Http404:
            messages.error(request, f"Matter with ID {matter_pk} not found.")
            # If matter not found, still show the user's documents but without matter filter
            # Or you could redirect to the unfiltered list: return redirect('documents:document_list')


    context = {
        'documents': documents,
        'form': DocumentUploadForm(), # Include the upload form on the list page (for general upload)
        'matter': matter, # Pass the matter object to the template if filtered
    }
    return render(request, 'documents/document_list.html', context)

@login_required # Require user to be logged in
def document_upload_view(request):
    """
    View to handle general document uploads (not specifically linked to a matter).
    """
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False) # Don't save yet
            document.uploaded_by = request.user # Assign the current user as uploader

            # Automatically set file_size and file_type before saving
            if document.file:
                document.file_size = document.file.size
                document.file_type = document.file.content_type or mimetypes.guess_type(document.file.name)[0] or 'application/octet-stream'

            document.save() # Save the document object

            # Handle ManyToManyField saves if your form includes them (e.g., linking clients)
            # form.save_m2m() # Uncomment if your form has ManyToManyFields

            messages.success(request, f'Document "{document.name}" uploaded successfully!')
            return redirect('documents:document_list') # Redirect to the document list (using namespace)

        else:
            # Display form errors and re-render the list page
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
            # Re-fetch documents for rendering the list page
            if request.user.is_superuser or request.user.role == 'admin':
                 documents = Document.objects.all()
            else:
                 documents = Document.objects.filter(uploaded_by=request.user)
            context = {
                 'documents': documents,
                 'form': form, # Pass the form with errors
            }
            return render(request, 'documents/document_list.html', context) # Render list with errors
    else:
        # GET request, redirect to the list page which includes the form
        return redirect('documents:document_list')


@login_required # Require user to be logged in
# @notary_required # Example: Only Notaries can upload for matters
def document_upload_for_matter_view(request, matter_pk):
    """
    View to handle document uploads specifically linked to a matter.
    """
    # Get the matter object or return 404
    matter = get_object_or_404(Matter, pk=matter_pk)

    # Permission check: Ensure the user has permission to upload for this matter
    # Example: User is admin, superuser, or assigned to the matter
    if not (request.user.is_superuser or
            request.user.role == 'admin' or
            request.user in matter.assigned_users.all()): # Assuming Matter has an assigned_users ManyToManyField
        messages.error(request, "You do not have permission to upload documents for this matter.")
        return redirect('workflows:matter_detail', pk=matter.pk) # Redirect back to the matter detail page

    if request.method == 'POST':
        # Use the standard DocumentUploadForm
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False) # Don't save yet
            document.uploaded_by = request.user # Assign the current user as uploader
            # Link the document to the matter
            document.matter = matter # Assuming 'matter' is a ForeignKey on the Document model

            # Automatically set file_size and file_type before saving
            if document.file:
                document.file_size = document.file.size
                document.file_type = document.file.content_type or mimetypes.guess_type(document.file.name)[0] or 'application/octet-stream'

            document.save() # Save the document object

            # If 'matter' is a ManyToManyField on Document, you would save m2m here:
            # form.save_m2m()
            # Or, if linking a document to a ManyToManyField on the Matter model:
            # matter.documents.add(document) # This assumes Matter has a 'documents' ManyToManyField


            messages.success(request, f'Document "{document.name}" uploaded successfully and linked to Matter "{matter.protocol_number}".')
            return redirect('workflows:matter_detail', pk=matter.pk) # Redirect back to the matter detail page (using namespace)

        else:
            # Display form errors and re-render the form page
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
            context = {
                 'form': form, # Pass the form with errors
                 'matter': matter, # Pass the matter object
                 'page_title': f'Upload Document for Matter: {matter.protocol_number}',
            }
            # Render the dedicated template for this specific upload case
            return render(request, 'documents/document_upload_for_matter.html', context)


    else:
        # GET request: Render the upload form specifically for this matter
        form = DocumentUploadForm()
        context = {
             'form': form,
             'matter': matter,
             'page_title': f'Upload Document for Matter: {matter.protocol_number}',
        }
        # Render the dedicated template for this specific upload case
        return render(request, 'documents/document_upload_for_matter.html', context)


@login_required # Require user to be logged in
def document_detail_view(request, pk):
    """
    View to display details of a specific document.
    Includes options to trigger AI processing.
    """
    # Get the document object, or return 404 if not found
    document = get_object_or_404(Document, pk=pk)

    # Ensure the user has permission to view this document
    # (e.g., they uploaded it, or they are an admin/have specific role,
    # or it's linked to a matter/client they have access to)
    if not (request.user.is_superuser or request.user.role == 'admin' or document.uploaded_by == request.user):
         # Add checks for client/matter linkage if implemented
         # from apps.clients.models import Client # Assuming Client model exists
         # from apps.workflows.models import Matter # Assuming Matter model exists
         # if not (
         #     (document.client and (request.user.is_superuser or request.user.role == 'admin' or document.client.created_by == request.user or request.user in document.client.assigned_users.all())) or
         #     (document.matter and (request.user.is_superuser or request.user.role == 'admin' or document.matter.created_by == request.user or request.user in document.matter.assigned_users.all()))
         # ):
         messages.error(request, "You do not have permission to view this document.")
         return redirect('documents:document_list') # Redirect to list if no permission (using namespace)

    context = {
        'document': document,
    }
    return render(request, 'documents/document_detail.html', context)

@login_required # Require user to be logged in
def document_delete_view(request, pk):
    """
    View to handle document deletion.
    """
    document = get_object_or_404(Document, pk=pk)

    # Ensure the user has permission to delete this document
    if not (request.user.is_superuser or request.user.role == 'admin' or document.uploaded_by == request.user):
         # Add checks for client/matter linkage if implemented
        messages.error(request, "You do not have permission to delete this document.")
        return redirect('documents:document_list') # Using namespace

    if request.method == 'POST':
        document_name = document.name # Get name before deleting
        document.delete() # This also deletes the file due to the model's delete method
        messages.success(request, f'Document "{document_name}" deleted successfully.')
        # Redirect back to the matter detail if the document was linked to a matter
        if document.matter:
            return redirect('workflows:matter_detail', pk=document.matter.pk)
        else:
            return redirect('documents:document_list') # Using namespace

    # For GET request, show a confirmation page (optional but recommended)
    context = {
        'document': document
    }
    return render(request, 'documents/document_confirm_delete.html', context)


@login_required # Require user to be logged in
def document_summarize_view(request, pk):
    """
    View to trigger AI summarization for a document.
    """
    document = get_object_or_404(Document, pk=pk)

    # Ensure the user has permission to process this document
    if not (request.user.is_superuser or request.user.role == 'admin' or document.uploaded_by == request.user):
         # Add checks for client/matter linkage if implemented
        messages.error(request, "You do not have permission to process this document.")
        return redirect('documents:document_detail', pk=pk) # Using namespace

    if request.method == 'POST':
        if document.file:
            try:
                # Update status to indicate processing
                document.status = 'processing'
                document.save()

                # Call the utility function to summarize
                # Consider running this in a background task for large documents
                summary = summarize_document(document.file.path)

                if summary:
                    document.summary = summary
                    document.status = 'processed'
                    document.save()
                    messages.success(request, f'Document "{document.name}" summarized successfully.')
                else:
                    document.status = 'error'
                    document.save()
                    messages.error(request, f'Failed to summarize document "{document.name}". Check logs.')

            except Exception as e:
                document.status = 'error'
                document.save()
                messages.error(request, f'An error occurred while summarizing document "{document.name}": {e}')
        else:
            messages.warning(request, f'Document "{document.name}" has no file attached.')

        return redirect('documents:document_detail', pk=pk) # Redirect back to document detail (using namespace)

    # For GET request, maybe show a confirmation or just redirect
    return redirect('documents:document_detail', pk=pk)


@login_required # Require user to be logged in
def document_segment_view(request, pk):
    """
    View to trigger AI segmentation for a document.
    """
    document = get_object_or_404(Document, pk=pk)

    # Ensure the user has permission to process this document
    if not (request.user.is_superuser or request.user.role == 'admin' or document.uploaded_by == request.user):
         # Add checks for client/matter linkage if implemented
        messages.error(request, "You do not have permission to process this document.")
        return redirect('documents:document_detail', pk=pk) # Using namespace

    if request.method == 'POST':
        if document.file:
            try:
                # Update status to indicate processing
                document.status = 'processing'
                document.save()

                # Call the utility function to segment
                # Consider running this in a background task
                segmentation_result = segment_document(document.file.path)

                if segmentation_result:
                    document.segmentation_result = segmentation_result
                    document.status = 'processed'
                    document.save()
                    messages.success(request, f'Document "{document.name}" segmented successfully.')
                else:
                    document.status = 'error'
                    document.save()
                    messages.error(request, f'Failed to segment document "{document.name}". Check logs.')

            except Exception as e:
                document.status = 'error'
                document.save()
                messages.error(request, f'An error occurred while segmenting document "{document.name}": {e}')
        else:
            messages.warning(request, f'Document "{document.name}" has no file attached.')

        return redirect('documents:document_detail', pk=pk) # Redirect back to document detail (using namespace)

    # For GET request, maybe show a confirmation or just redirect
    return redirect('documents:document_detail', pk=pk)


# Add views for other document operations (editing, QES, etc.) later
@login_required
# @notary_required # Example: Only Notaries/Admins can edit documents
def document_edit_view(request, pk):
    """View to edit document metadata."""
    document = get_object_or_404(Document, pk=pk)
    # Permission check
    if not (request.user.is_superuser or request.user.role == 'admin' or document.uploaded_by == request.user):
         # Add checks for client/matter linkage if implemented
        messages.error(request, "You do not have permission to edit this document.")
        return redirect('documents:document_detail', pk=pk) # Using namespace

    if request.method == 'POST':
        # Pass the document instance to the form to update the existing document
        form = DocumentEditForm(request.POST, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "Document metadata updated.")
            return redirect('documents:document_detail', pk=pk) # Using namespace
    else:
        # Populate the form with the current document's data
        form = DocumentEditForm(instance=document)
    # This view requires a template named 'documents/document_edit.html'
    return render(request, 'documents/document_edit.html', {'form': form, 'document': document})

@login_required
# @notary_required # Example: Only Notaries/Admins can convert documents
def document_convert_view(request, pk):
    """View to trigger document conversion (e.g., to PDF)."""
    document = get_object_or_404(Document, pk=pk)
    # Permission check
    if not (request.user.is_superuser or request.user.role == 'admin' or document.uploaded_by == request.user):
         # Add checks for client/matter linkage if implemented
        messages.error(request, "You do not have permission to convert this document.")
        return redirect('documents:document_detail', pk=pk) # Using namespace

    if request.method == 'POST':
        # Placeholder for conversion logic
        messages.info(request, f"Conversion of document '{document.name}' triggered (placeholder).")
        # Call a utility function for conversion here
        # success, message, converted_file_path = convert_to_pdf(document.file.path, output_dir)
        # Update document model with converted file and status

        # For now, just redirect back
        return redirect('documents:document_detail', pk=pk) # Using namespace

    # For GET request, maybe show a confirmation page or just redirect
    return redirect('documents:document_detail', pk=pk)

@login_required
# @notary_required # Example: Only Notaries/Admins can apply QES
def document_apply_qes_view(request, pk):
    """View to trigger applying QES."""
    document = get_object_or_404(Document, pk=pk)
    # Permission check
    if not (request.user.is_superuser or request.user.role == 'admin' or document.uploaded_by == request.user):
         # Add checks for client/matter linkage if implemented
        messages.error(request, "You do not have permission to apply QES to this document.")
        return redirect('documents:document_detail', pk=pk) # Using namespace

    if request.method == 'POST':
        # Placeholder for QES application logic
        messages.info(request, f"QES application triggered for document '{document.name}' (placeholder).")
        # Call a utility function for QES here
        # success, message, signed_file_path = apply_qes(document.file.path, signature_data)
        # Update document model with signed file and status

        # For now, just redirect back
        return redirect('documents:document_detail', pk=pk) # Using namespace

    # For GET request, maybe show a confirmation page or just redirect
    return redirect('documents:document_detail', pk=pk)

@login_required
# @notary_required # Example: Only Notaries/Admins can download documents
def document_download_view(request, pk):
    """View to download the document file."""
    document = get_object_or_404(Document, pk=pk)
     # Permission check
    if not (request.user.is_superuser or request.user.role == 'admin' or document.uploaded_by == request.user):
        messages.error(request, "You do not have permission to download this document.")
        return redirect('documents:document_list') # Using namespace

    if document.file:
        # Use default_storage to handle different storage backends
        file_path = document.file.path
        if default_storage.exists(file_path):
            with default_storage.open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type=document.file_type)
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(document.file.name)}"'
                return response
        else:
            # If the file is expected but not found on storage
            messages.error(request, "Document file not found on storage.")
            return redirect('documents:document_detail', pk=pk) # Redirect back to detail (using namespace)
            # Alternatively, raise Http404("Document file not found.")
    else:
        messages.warning(request, "No file attached to this document record.")
        return redirect('documents:document_detail', pk=pk) # Using namespace
