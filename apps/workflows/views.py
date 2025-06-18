# apps/workflows/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q # For searching
from django.forms import inlineformset_factory # For managing WorkflowSteps within a Workflow
import logging
from .models import Matter, Workflow, WorkflowStep, WorkflowTemplate
from .forms import MatterForm, WorkflowForm, WorkflowStepForm
from .utils import generate_workflow_steps_ai # Import AI utility
# Import custom decorators from accounts app for role-based access control
from apps.accounts.utils import admin_required, notary_required, solicitor_required, paid_user_required
from apps.documents.models import Document


logger = logging.getLogger(__name__)
# Define the inline formset for Workflow Steps
WorkflowStepFormSet = inlineformset_factory(
    Workflow, # Parent model
    WorkflowStep, # Child model
    form=WorkflowStepForm,
    extra=1, # Number of empty forms to display initially
    can_delete=True, # Allow deleting steps
    fields = ['step_template', 'name', 'description', 'order', 'status', 'assigned_to', 'due_date', 'notes'] # Fields to include
)


@login_required
# @paid_user_required # Example: Only paid users can view matters
def matter_list_view(request):
    """
    View to list all matters.
    Filter based on user role and assigned matters.
    Includes search functionality.
    """
    # Base queryset - filter based on user permissions
    if request.user.is_superuser or request.user.role == 'admin':
        matters = Matter.objects.all() # Admin sees all matters
    else:
        # Users see matters they created or are assigned to
        matters = Matter.objects.filter(Q(created_by=request.user) | Q(assigned_users=request.user)).distinct()

    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        matters = matters.filter(
            Q(protocol_number__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(clients__first_name__icontains=search_query) |
            Q(clients__last_name__icontains=search_query) |
            Q(clients__business_name__icontains=search_query) |
            Q(notes__icontains=search_query)
        ).distinct() # Use distinct() because of the join on clients

    context = {
        'matters': matters,
        'search_query': search_query,
    }
    return render(request, 'workflows/matter_list.html', context)
from django.db import IntegrityError
@login_required
def matter_create_view(request):
    logger.debug("Entering matter_create_view")
    
    if request.method == 'POST':
        logger.debug("Received POST request: %s", request.POST)
        form = MatterForm(request.POST)
        
        if form.is_valid():
            logger.debug("Form is valid")
            try:
                matter = form.save(commit=False)
                matter.created_by = request.user
                matter.save()
                form.save_m2m()  # Save many-to-many relationships
                
                messages.success(request, f'Matter "{matter.protocol_number}" created successfully!')
                logger.info("Matter %s created by user %s", matter.protocol_number, request.user)
                return redirect('workflows:matter_detail', pk=matter.pk)
                
            except IntegrityError as e:
                logger.error("IntegrityError: %s", e)
                messages.error(request, "A matter with this protocol number already exists.")
            except Exception as e:
                logger.error("Unexpected error in matter_create_view: %s", e, exc_info=True)
                messages.error(request, "An unexpected error occurred while creating the matter.")
        else:
            logger.debug("Form is invalid: %s", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = MatterForm()
        logger.debug("Rendering GET request for matter creation form")
    
    context = {
        'form': form,
        'page_title': 'Create New Matter',
    }
    return render(request, 'workflows/matter_form.html', context)
def matter_detail_view(request, pk):
    matter = get_object_or_404(Matter, pk=pk)
    
    # Permission check
    if not (request.user.is_superuser 
            or request.user.role == 'admin' 
            or matter.created_by == request.user 
            or request.user in matter.assigned_users.all()):
        messages.error(request, "Permission denied")
        return redirect('workflows:matter_list')

    try:
        workflow = matter.workflow
        workflow_steps = workflow.steps.all().order_by('order')
    except Workflow.DoesNotExist:
        workflow = None
        workflow_steps = []

    context = {
        'matter': matter,
        'workflow': workflow,
        'workflow_steps': workflow_steps,
        'documents': matter.documents.all().order_by('-upload_date')
    }
    return render(request, 'workflows/matter_detail.html', context)

@login_required
# @paid_user_required # Example: Only paid users can update matters
def matter_update_view(request, pk):
    """
    View to update an existing matter.
    """
    matter = get_object_or_404(Matter, pk=pk)

    # Permission check: Ensure user can edit this matter
    if not (request.user.is_superuser or request.user.role == 'admin' or matter.created_by == request.user or request.user in matter.assigned_users.all()):
        messages.error(request, "You do not have permission to edit this matter.")
        return redirect('matter_detail', pk=pk)

    if request.method == 'POST':
        form = MatterForm(request.POST, instance=matter)
        # You might need to pass the user to the form to filter client/assigned user choices
        # form = MatterForm(request.POST, instance=matter, user=request.user)
        if form.is_valid():
            matter = form.save() # Save the updated matter (includes ManyToManyField saves)

            messages.success(request, f'Matter "{matter.protocol_number}" updated successfully!')
            return redirect('matter_detail', pk=matter.pk) # Redirect to the detail page
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = MatterForm(instance=matter) # Populate form with existing matter data
        # You might need to pass the user to the form to filter client/assigned user choices
        # form = MatterForm(instance=matter, user=request.user)


    context = {
        'form': form,
        'matter': matter,
        'page_title': f'Edit Matter: {matter.protocol_number}',
    }
    return render(request, 'workflows/matter_form.html', context)

@login_required
# @paid_user_required # Example: Only paid users can delete matters
def matter_delete_view(request, pk):
    """
    View to handle matter deletion.
    """
    matter = get_object_or_404(Matter, pk=pk)

    # Permission check: Ensure user can delete this matter
    if not (request.user.is_superuser or request.user.role == 'admin' or matter.created_by == request.user): # Only creator or admin can delete?
        messages.error(request, "You do not have permission to delete this matter.")
        return redirect('matter_detail', pk=pk)

    if request.method == 'POST':
        matter_identifier = matter.protocol_number # Get identifier before deleting
        matter.delete() # Delete the matter object (related Workflow and Steps will be deleted due to CASCADE)
        messages.success(request, f'Matter "{matter_identifier}" deleted successfully.')
        return redirect('matter_list') # Redirect to the matter list

    # For GET request, show a confirmation page
    context = {
        'matter': matter
    }
    return render(request, 'workflows/matter_confirm_delete.html', context)


@login_required
# @notary_required # Example: Only Notaries can manage workflows
def workflow_detail_view(request, matter_pk):
    """
    View to display and manage the workflow for a specific matter.
    Includes viewing steps and managing step statuses.
    Uses a formset to edit steps.
    """
    matter = get_object_or_404(Matter, pk=matter_pk)

    # Permission check: Ensure user can view/manage workflow for this matter
    if not (request.user.is_superuser or request.user.role == 'admin' or matter.created_by == request.user or request.user in matter.assigned_users.all()):
        messages.error(request, "You do not have permission to manage the workflow for this matter.")
        return redirect('matter_detail', pk=matter_pk)

    try:
        workflow = matter.workflow # Get the related workflow
    except Workflow.DoesNotExist:
        # If no workflow exists, offer to create one
        messages.info(request, "No workflow exists for this matter. You can create one.")
        return redirect('workflow_create', matter_pk=matter_pk)


    if request.method == 'POST':
        formset = WorkflowStepFormSet(request.POST, request.FILES, instance=workflow)
        if formset.is_valid():
            formset.save() # Save the steps (creates, updates, deletes)

            # Optional: Update workflow status based on step statuses
            # update_workflow_status(workflow) # Implement this utility function

            messages.success(request, 'Workflow steps updated successfully.')
            return redirect('workflow_detail', matter_pk=matter.pk) # Redirect back to workflow detail
        else:
            # Display formset errors
            messages.error(request, 'Please correct the errors below.')
            # Formset errors are usually attached to the forms within the formset

    else:
        # GET request: Initialize the formset with existing steps
        formset = WorkflowStepFormSet(instance=workflow)

    context = {
        'matter': matter,
        'workflow': workflow,
        'formset': formset,
    }
    return render(request, 'workflows/workflow_detail.html', context)

@login_required
# @notary_required # Example: Only Notaries can create workflows
def workflow_create_view(request, matter_pk):
    """
    View to create a new workflow for a specific matter.
    Allows selecting a template or creating a custom workflow.
    """
    matter = get_object_or_404(Matter, pk=matter_pk)

    # Permission check: Ensure user can create workflow for this matter
    if not (request.user.is_superuser or request.user.role == 'admin' or matter.created_by == request.user or request.user in matter.assigned_users.all()):
        messages.error(request, "You do not have permission to create a workflow for this matter.")
        return redirect('matter_detail', pk=matter_pk)

    # Check if a workflow already exists for this matter
    try:
        existing_workflow = matter.workflow
        messages.warning(request, "A workflow already exists for this matter.")
        return redirect('workflow_detail', matter_pk=matter.pk)
    except Workflow.DoesNotExist:
        pass # No workflow exists, proceed with creation


    if request.method == 'POST':
        form = WorkflowForm(request.POST)
        if form.is_valid():
            workflow = form.save(commit=False)
            workflow.matter = matter # Link the workflow to the matter
            workflow.save() # Save the workflow object

            # If a template was selected, create steps from the template
            template = form.cleaned_data.get('template')
            if template:
                step_templates = WorkflowStepTemplate.objects.filter(template=template).order_by('order')
                for step_template in step_templates:
                    WorkflowStep.objects.create(
                        workflow=workflow,
                        step_template=step_template,
                        name=step_template.name,
                        description=step_template.description,
                        order=step_template.order,
                        status='not_started' # Initial status for steps
                    )
                messages.success(request, f"Workflow created from template '{template.name}'. Steps added.")
            else:
                 messages.success(request, "Custom workflow created. Add steps below.")


            # Optional: Trigger AI step generation if no template was selected
            # if not template:
            #     ai_steps = generate_workflow_steps_ai(matter.title, matter.description)
            #     if ai_steps:
            #         workflow.ai_generated_steps = ai_steps
            #         workflow.save()
            #         messages.info(request, "AI suggested steps have been generated. Review and add them.")


            return redirect('workflow_detail', matter_pk=matter.pk) # Redirect to the workflow detail page

        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = WorkflowForm()

    context = {
        'form': form,
        'matter': matter,
        'page_title': f'Create Workflow for Matter: {matter.protocol_number}',
    }
    return render(request, 'workflows/workflow_form.html', context)


@login_required
# @notary_required # Example: Only Notaries can trigger AI steps
def workflow_trigger_ai_steps_view(request, workflow_pk):
    """
    View to trigger AI workflow step generation for a specific workflow.
    """
    workflow = get_object_or_404(Workflow, pk=workflow_pk)
    matter = workflow.matter # Get the related matter

    # Permission check: Ensure user can trigger AI for this workflow/matter
    if not (request.user.is_superuser or request.user.role == 'admin' or matter.created_by == request.user or request.user in matter.assigned_users.all()):
        messages.error(request, "You do not have permission to trigger AI steps for this workflow.")
        return redirect('workflow_detail', matter_pk=matter.pk)

    if request.method == 'POST':
        if matter:
            try:
                # Call the utility function
                # Consider running this in a background task
                steps_list = generate_workflow_steps_ai(matter.title, matter.description)

                if steps_list:
                    workflow.ai_generated_steps = steps_list
                    workflow.save()
                    messages.success(request, "AI suggested steps have been generated. Review them below.")
                else:
                    messages.warning(request, "AI failed to generate steps.")

            except Exception as e:
                messages.error(request, f'An error occurred while generating AI steps: {e}')
        else:
            messages.warning(request, 'This workflow is not linked to a matter.')

        return redirect('workflow_detail', matter_pk=matter.pk) # Redirect back to workflow detail

    # For GET request, maybe show a confirmation or just redirect
    return redirect('workflow_detail', matter_pk=matter.pk)

# Add views for managing Workflow Templates and Workflow Step Templates if needed
# These might be primarily managed via the Django Admin interface.
@login_required
@admin_required  # Only admin can manage templates
def workflow_template_list_view(request):
    """View to list workflow templates."""
    templates = WorkflowTemplate.objects.all()
    context = {'templates': templates}
    return render(request, 'workflows/workflow_template_list.html', context)

@login_required
@admin_required
def workflow_template_detail_view(request, pk):
    """View to display details of a workflow template."""
    template = get_object_or_404(WorkflowTemplate, pk=pk)
    step_templates = template.step_templates.all()
    context = {'template': template, 'step_templates': step_templates}
    return render(request, 'workflows/workflow_template_detail.html', context)
