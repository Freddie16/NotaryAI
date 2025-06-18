# apps/clients/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q  # For searching

from .models import Client  # , Lead  # Uncomment Lead if you create that model
from .forms import ClientForm  # , LeadForm  # Uncomment LeadForm if you create that form
from .utils import generate_segmentation_tags  # Import AI utility
# Import custom decorators from accounts app for role-based access control
from apps.accounts.utils import admin_required, notary_required, solicitor_required, paid_user_required

@login_required
# @paid_user_required # Example: Only paid users can view clients
def client_list_view(request):
    """
    View to list all clients.
    Filter based on user role and potentially assigned clients.
    Includes search functionality.
    """
    # Base queryset - filter based on user permissions
    if request.user.is_superuser or request.user.role == 'admin':
        clients = Client.objects.all()  # Admin sees all clients
    elif request.user.role in ['notary', 'solicitor']:
        # Notaries/Solicitors might see clients they created or are assigned to
        # Assuming Client model has a 'created_by' field. You might add an 'assigned_users' ManyToManyField.
        clients = Client.objects.filter(created_by=request.user)
        # If you add assignment: clients = Client.objects.filter(Q(created_by=request.user) | Q(assigned_users=request.user)).distinct()
    else:
        # Paid users might only see clients they created
        clients = Client.objects.filter(created_by=request.user)

    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        clients = clients.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(business_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    context = {
        'clients': clients,
        'search_query': search_query,
    }
    return render(request, 'clients/client_list.html', context)

@login_required
# @paid_user_required # Example: Only paid users can create clients
def client_create_view(request):
    """
    View to create a new client.
    """
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)  # Don't save yet
            client.created_by = request.user  # Assign the current user as creator
            client.save()  # Save the client object

            # Optional: Trigger AI segmentation after saving
            # Consider running this in a background task
            # segmentation_tags = generate_segmentation_tags(client)
            # if segmentation_tags:
            #     client.segmentation_tags = segmentation_tags
            #     client.save()

            messages.success(request, f'Client "{client.__str__()}" created successfully!')
            return redirect('client_detail', pk=client.pk)  # Redirect to the detail page
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = ClientForm()

    context = {
        'form': form,
        'page_title': 'Create New Client',
    }
    return render(request, 'clients/client_form.html', context)

@login_required
# @paid_user_required # Example: Only paid users can view client details
def client_detail_view(request, pk):
    """
    View to display details of a specific client.
    Includes linked documents, compliance checks, matters, etc.
    """
    client = get_object_or_404(Client, pk=pk)

    # Permission check: Ensure user can view this client
    if not (request.user.is_superuser or request.user.role == 'admin' or client.created_by == request.user):
        # Add checks for assignment if implemented
        # or request.user in client.assigned_users.all()
        messages.error(request, "You do not have permission to view this client.")
        return redirect('client_list')

    # Fetch related objects (assuming these models exist in other apps)
    # linked_documents = client.document_set.all() # Assuming a ForeignKey from Document to Client
    # linked_compliance_checks = client.compliancecheck_set.all() # Assuming a ForeignKey from ComplianceCheck to Client
    # linked_matters = client.matter_set.all() # Assuming a ForeignKey from Matter to Client

    context = {
        'client': client,
        # 'linked_documents': linked_documents, # Add to context if fetched
        # 'linked_compliance_checks': linked_compliance_checks,
        # 'linked_matters': linked_matters,
    }
    return render(request, 'clients/client_detail.html', context)

@login_required
# @paid_user_required # Example: Only paid users can edit clients
def client_update_view(request, pk):
    """
    View to update an existing client.
    """
    client = get_object_or_404(Client, pk=pk)

    # Permission check: Ensure user can edit this client
    if not (request.user.is_superuser or request.user.role == 'admin' or client.created_by == request.user):
        # Add checks for assignment if implemented
        messages.error(request, "You do not have permission to edit this client.")
        return redirect('client_detail', pk=pk)

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save()  # Save the updated client

            # Optional: Re-trigger AI segmentation after update
            # Consider running this in a background task
            # segmentation_tags = generate_segmentation_tags(client)
            # if segmentation_tags:
            #     client.segmentation_tags = segmentation_tags
            #     client.save()

            messages.success(request, f'Client "{client.__str__()}" updated successfully!')
            return redirect('client_detail', pk=client.pk)  # Redirect to the detail page
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = ClientForm(instance=client)  # Populate form with existing client data

    context = {
        'form': form,
        'client': client,
        'page_title': f'Edit Client: {client.__str__()}',
    }
    return render(request, 'clients/client_form.html', context)

@login_required
# @paid_user_required # Example: Only paid users can delete clients
def client_delete_view(request, pk):
    """
    View to handle client deletion.
    """
    client = get_object_or_404(Client, pk=pk)

    # Permission check: Ensure user can delete this client
    if not (request.user.is_superuser or request.user.role == 'admin' or client.created_by == request.user):
        # Add checks for assignment if implemented
        messages.error(request, "You do not have permission to delete this client.")
        return redirect('client_detail', pk=pk)

    if request.method == 'POST':
        client_name = client.__str__()  # Get name before deleting
        client.delete()  # Delete the client object
        messages.success(request, f'Client "{client_name}" deleted successfully.')
        return redirect('client_list')  # Redirect to the client list

    # For GET request, show a confirmation page
    context = {
        'client': client
    }
    return render(request, 'clients/client_confirm_delete.html', context)


# Example views for Lead management (if you create a separate Lead model)
@login_required
@paid_user_required
def lead_list_view(request):
    """View to list leads.""" 
    leads = Lead.objects.filter(assigned_to=request.user)  # Example: show leads assigned to user
    if request.user.is_superuser or request.user.role == 'admin':
        leads = Lead.objects.all()  # Admin sees all leads
    context = {'leads': leads}
    return render(request, 'clients/lead_list.html', context)

@login_required
@paid_user_required
def lead_create_view(request):
    """View to create a new lead.""" 
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.assigned_to = request.user  # Assign lead creator
            lead.save()
            messages.success(request, f'Lead "{lead.name}" created.')
            return redirect('lead_list')
    else:
        form = LeadForm()
    context = {'form': form, 'page_title': 'Create New Lead'}
    return render(request, 'clients/lead_form.html', context)

@login_required
@paid_user_required
def lead_detail_view(request, pk):
    """View to display details of a specific lead.""" 
    lead = get_object_or_404(Lead, pk=pk)
    # Permission check
    if not (request.user.is_superuser or request.user.role == 'admin' or lead.assigned_to == request.user):
        messages.error(request, "You do not have permission to view this lead.")
        return redirect('lead_list')
    context = {'lead': lead}
    return render(request, 'clients/lead_detail.html', context)

@login_required
@paid_user_required
def lead_convert_to_client_view(request, pk):
    """View to convert a lead to a client.""" 
    lead = get_object_or_404(Lead, pk=pk)
    # Permission check
    if not (request.user.is_superuser or request.user.role == 'admin' or lead.assigned_to == request.user):
        messages.error(request, "You do not have permission to convert this lead.")
        return redirect('lead_detail', pk=pk)

    if request.method == 'POST':
        # Implement conversion logic in utils or here
        client = convert_lead_to_client(lead)  # Call utility function
        if client:
            lead.delete()  # Delete the lead after conversion
            messages.success(request, f'Lead "{lead.name}" converted to client.')
            return redirect('client_detail', pk=client.pk)
        else:
            messages.error(request, 'Failed to convert lead to client.')
            return redirect('lead_detail', pk=pk)
    # For GET, maybe show a confirmation page
    context = {'lead': lead}
    return render(request, 'clients/lead_confirm_convert.html', context)
