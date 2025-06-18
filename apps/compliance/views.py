# apps/compliance/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import formset_factory # To handle multiple answer forms
from django.db import transaction # For atomic database operations
# Import necessary modules for webhook views
from django.views.decorators.csrf import csrf_exempt # Might need to exempt CSRF for API endpoints
from django.http import JsonResponse
import json # To parse incoming JSON data

from .models import (
    ComplianceWorkflowTemplate,
    ComplianceQuestion,
    ComplianceWorkflowTemplateQuestion,
    ComplianceCheck,
    ComplianceAnswer
)
from .forms import ComplianceCheckInitiateForm, ComplianceAnswerForm
from .utils import trigger_credas_check, trigger_peps_sanctions_check # Import utility functions
# Import custom decorators from accounts app if needed for role-based access
# Uncomment the decorators you intend to use
from apps.accounts.utils import notary_required, admin_required, solicitor_required, paid_user_required # Uncommented import

# Define a formset for answering questions
# We'll create this dynamically in the view or using formsets.
# Here's a basic idea for a single answer form:
# ComplianceAnswerFormSet = formset_factory(ComplianceAnswerForm, extra=0) # Basic formset factory

@login_required
# @paid_user_required # Example: Only paid users can view compliance checks
def compliance_check_list_view(request):
    """
    View to list all compliance checks.
    Filter based on user role and potentially assigned checks.
    """
    if request.user.is_superuser or request.user.role == 'admin':
        compliance_checks = ComplianceCheck.objects.all()
    else:
        # Filter checks based on user's clients or matters (requires Client/Matter models)
        # compliance_checks = ComplianceCheck.objects.filter(client__in=request.user.clients.all()) | \
        #                   ComplianceCheck.objects.filter(matter__in=request.user.matters.all()) # Example filtering
        # For now, just show checks initiated by the user if no client/matter linkage
        compliance_checks = ComplianceCheck.objects.filter(initiated_by=request.user)


    context = {
        'compliance_checks': compliance_checks,
    }
    return render(request, 'compliance/compliance_check_list.html', context)

@login_required
# @notary_required # Example: Only Notaries can initiate checks
def compliance_check_initiate_view(request):
    """
    View to initiate a new compliance check.
    Allows selecting a template and linking to a client/matter.
    """
    if request.method == 'POST':
        form = ComplianceCheckInitiateForm(request.POST)
        # You might need to pass the user to the form to filter client/matter choices
        # form = ComplianceCheckInitiateForm(request.POST, user=request.user)
        if form.is_valid():
            compliance_check = form.save(commit=False)
            compliance_check.initiated_by = request.user
            compliance_check.status = 'pending' # Initial status
            # Set client/matter here if the form includes them and they are valid
            # compliance_check.client = form.cleaned_data.get('client')
            # compliance_check.matter = form.cleaned_data.get('matter')
            compliance_check.save()

            # If a template is selected, create initial answers for its questions
            if compliance_check.template:
                questions = ComplianceWorkflowTemplateQuestion.objects.filter(template=compliance_check.template).order_by('order')
                for template_question in questions:
                    # Create a blank answer object for each question in the template
                    ComplianceAnswer.objects.create(
                        compliance_check=compliance_check,
                        question=template_question.question,
                        answered_by=None # Answered by will be set when the answer is submitted
                    )

            messages.success(request, f'Compliance check #{compliance_check.pk} initiated successfully.')
            return redirect('compliance_check_detail', pk=compliance_check.pk) # Redirect to the detail page

        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = ComplianceCheckInitiateForm()
        # You might need to pass the user to the form to filter client/matter choices
        # form = ComplianceCheckInitiateForm(user=request.user)

    context = {
        'form': form,
    }
    return render(request, 'compliance/compliance_check_initiate.html', context)

@login_required
# @notary_required # Example: Only Notaries can view check details
def compliance_check_detail_view(request, pk):
    """
    View to display details of a specific compliance check.
    Includes status, linked client/matter, answers, and options for external checks.
    """
    compliance_check = get_object_or_404(ComplianceCheck, pk=pk)

    # Permission check: Ensure user can view this check
    # Example: user is admin, initiated the check, or linked to client/matter
    if not (request.user.is_superuser or request.user.role == 'admin' or compliance_check.initiated_by == request.user):
         # Add checks for client/matter linkage if implemented
         # or compliance_check.client and compliance_check.client in request.user.clients.all()
         # or compliance_check.matter and compliance_check.matter in request.user.matters.all()
        messages.error(request, "You do not have permission to view this compliance check.")
        return redirect('compliance_check_list')

    # Get answers related to this check
    answers = compliance_check.answers.all()

    context = {
        'compliance_check': compliance_check,
        'answers': answers,
    }
    return render(request, 'compliance/compliance_check_detail.html', context)


@login_required
# @notary_required # Example: Only Notaries can answer questions
def compliance_check_answer_questions_view(request, pk):
    """
    View to answer questions for a specific compliance check.
    Uses a formset to handle multiple answers.
    """
    compliance_check = get_object_or_404(ComplianceCheck, pk=pk)

    # Permission check: Ensure user can answer questions for this check
    if not (request.user.is_superuser or request.user.role == 'admin' or compliance_check.initiated_by == request.user):
         # Add checks for client/matter linkage if implemented
        messages.error(request, "You do not have permission to answer questions for this compliance check.")
        return redirect('compliance_check_detail', pk=pk)

    # Get the questions associated with this check (either from template or custom)
    # If using a template, get questions from the template
    if compliance_check.template:
        questions = [tq.question for tq in ComplianceWorkflowTemplateQuestion.objects.filter(template=compliance_check.template).order_by('order')]
    else:
        # If not using a template, you might have custom questions linked directly
        # For now, assume questions are only from templates or need to be added manually
        questions = [] # Or fetch custom questions linked to the check

    # Create a formset factory for the answers
    # We need to pass initial data for existing answers
    initial_data = []
    existing_answers = {answer.question_id: answer for answer in compliance_check.answers.all()}

    for question in questions:
        initial_answer = existing_answers.get(question.id)
        initial_data.append({
            'question': question, # Pass the question object to the form
            'answer_text': initial_answer.answer_text if initial_answer else None,
            'answer_boolean': initial_answer.answer_boolean if initial_answer else None,
            'answer_choice': initial_answer.answer_choice if initial_answer else None,
            'answer_date': initial_answer.answer_date if initial_answer else None,
            'answer_file': initial_answer.answer_file if initial_answer else None,
            # Include the existing answer ID if updating
            'id': initial_answer.id if initial_answer else None,
        })

    # Create a formset factory dynamically to include the question object
    # This is a common pattern with formsets for related objects
    ComplianceAnswerFormSet = formset_factory(ComplianceAnswerForm, extra=0)

    if request.method == 'POST':
        formset = ComplianceAnswerFormSet(request.POST, request.FILES, initial=initial_data)
        if formset.is_valid():
            with transaction.atomic(): # Use atomic transaction for data integrity
                for form in formset:
                    # Get the question object from the initial data
                    question = form.initial.get('question')
                    answer_id = form.initial.get('id') # Get existing answer ID if present

                    if answer_id:
                        # Update existing answer
                        answer = ComplianceAnswer.objects.get(id=answer_id)
                        answer.answer_text = form.cleaned_data.get('answer_text')
                        answer.answer_boolean = form.cleaned_data.get('answer_boolean')
                        answer.answer_choice = form.cleaned_data.get('answer_choice')
                        answer.answer_date = form.cleaned_data.get('answer_date')
                        # Handle file upload update if needed
                        if 'answer_file' in form.cleaned_data and form.cleaned_data['answer_file']:
                            answer.answer_file = form.cleaned_data['answer_file']
                        answer.answered_by = request.user
                        answer.save()
                    else:
                        # Create new answer
                        # Ensure the form has the question and compliance_check linked
                        # This requires passing them when creating the form instance or formset
                        # A simpler approach is to get the question from initial data as done above
                        # and create the Answer object manually or use a custom formset.
                        # For simplicity here, we'll get the question from initial data.
                        if question: # Ensure question object exists
                            ComplianceAnswer.objects.create(
                                compliance_check=compliance_check,
                                question=question,
                                answer_text=form.cleaned_data.get('answer_text'),
                                answer_boolean=form.cleaned_data.get('answer_boolean'),
                                answer_choice=form.cleaned_data.get('answer_choice'),
                                answer_date=form.cleaned_data.get('answer_date'),
                                answer_file=form.cleaned_data.get('answer_file'),
                                answered_by=request.user
                            )
                        else:
                            # Handle case where question is missing (shouldn't happen with correct initial data)
                            messages.error(request, "Error: Missing question data for one or more answers.")
                            # You might want to log this error

            # Update compliance check status if all required questions are answered
            # This logic can be more complex depending on your requirements
            # For example, check if all questions in the template have non-null answers
            # if all_required_questions_answered(compliance_check):
            #     compliance_check.status = 'requires_review' # Or 'in_progress'
            #     compliance_check.save()

            messages.success(request, 'Compliance answers saved successfully.')
            return redirect('compliance_check_detail', pk=compliance_check.pk) # Redirect back to detail page
        else:
            # Display formset errors
            messages.error(request, 'Please correct the errors below.')
            # Formset errors are usually attached to the forms within the formset
            # You can iterate through formset.forms and form.errors to display them

    else:
        # GET request: Initialize the formset with existing answers
        formset = ComplianceAnswerFormSet(initial=initial_data)

    # Pass the questions and formset to the template
    # You might need to zip questions and forms together in the template for rendering
    context = {
        'compliance_check': compliance_check,
        'questions': questions, # Pass questions to help with rendering
        'formset': formset,
    }
    return render(request, 'compliance/compliance_check_answer_questions.html', context)


@login_required
# @notary_required # Example: Only Notaries can trigger external checks
def compliance_check_trigger_credas_view(request, pk):
    """
    View to trigger a Credas check for a compliance check's client.
    """
    compliance_check = get_object_or_404(ComplianceCheck, pk=pk)

    # Permission check
    if not (request.user.is_superuser or request.user.role == 'admin' or compliance_check.initiated_by == request.user):
         # Add checks for client/matter linkage if implemented
        messages.error(request, "You do not have permission to trigger external checks for this compliance check.")
        return redirect('compliance_check_detail', pk=pk)

    if request.method == 'POST':
        if compliance_check.client:
            # Call the utility function
            # Consider running this in a background task for better performance
            success, message, check_id = trigger_credas_check(compliance_check.client)

            if success:
                compliance_check.credas_check_id = check_id
                # Update status to reflect that an external check is in progress
                if compliance_check.status not in ['in_progress', 'requires_review']:
                     compliance_check.status = 'in_progress'
                compliance_check.save()
                messages.success(request, f'Credas check initiated. Reference ID: {check_id}')
            else:
                messages.error(request, f'Failed to initiate Credas check: {message}')
                # Optionally update check status to error if initiation fails
                # compliance_check.status = 'error'
                # compliance_check.save()
        else:
            messages.warning(request, 'This compliance check is not linked to a client. Cannot trigger Credas check.')

        return redirect('compliance_check_detail', pk=pk) # Redirect back to detail page

    # For GET request, maybe show a confirmation or just redirect
    return redirect('compliance_check_detail', pk=pk)


@login_required
# @notary_required # Example: Only Notaries can trigger external checks
def compliance_check_trigger_peps_sanctions_view(request, pk):
    """
    View to trigger a PEPs and sanctions check for a compliance check's client.
    """
    compliance_check = get_object_or_404(ComplianceCheck, pk=pk)

    # Permission check
    if not (request.user.is_superuser or request.user.role == 'admin' or compliance_check.initiated_by == request.user):
         # Add checks for client/matter linkage if implemented
        messages.error(request, "You do not have permission to trigger external checks for this compliance check.")
        return redirect('compliance_check_detail', pk=pk)

    if request.method == 'POST':
        if compliance_check.client:
            # Call the utility function
            # Consider running this in a background task
            success, message, check_id = trigger_peps_sanctions_check(compliance_check.client)

            if success:
                compliance_check.peps_sanctions_check_id = check_id
                 # Update status
                if compliance_check.status not in ['in_progress', 'requires_review']:
                     compliance_check.status = 'in_progress'
                compliance_check.save()
                messages.success(request, f"PEPs/Sanctions check initiated. Reference ID: {check_id}")
            else:
                messages.error(request, f"Failed to initiate PEPs/Sanctions check: {message}")
                 # Optionally update check status to error
                # compliance_check.status = 'error'
                # compliance_check.save()
        else:
            messages.warning(request, 'This compliance check is not linked to a client. Cannot trigger PEPs/Sanctions check.')

        return redirect('compliance_check_detail', pk=pk) # Redirect back to detail page

    # For GET request, maybe show a confirmation or just redirect
    return redirect('compliance_check_detail', pk=pk)


# Add views for retrieving results from external checks (might be triggered by webhooks)
@csrf_exempt # Be cautious with CSRF exemption - implement proper webhook security
def credas_webhook_view(request):
    """Webhook endpoint to receive results from Credas."""
    # Implement webhook verification (e.g., check signature, IP address)
    # This is crucial for security!
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            # Process the webhook payload
            # Find the relevant ComplianceCheck using the check_id from the payload
            credas_check_id = payload.get('check_id')
            status = payload.get('status') # e.g., 'completed', 'failed'
            result_data = payload.get('result') # Detailed result data

            if credas_check_id:
                try:
                    compliance_check = ComplianceCheck.objects.get(credas_check_id=credas_check_id)
                    # Update the compliance check based on the webhook data
                    # Example:
                    # compliance_check.credas_status = status
                    # compliance_check.credas_result_data = result_data # Store results
                    # Update overall compliance check status if needed
                    # if status == 'completed':
                    #     compliance_check.status = 'requires_review' # Ready for internal review
                    # elif status == 'failed':
                    #      compliance_check.status = 'failed'
                    # compliance_check.save()
                    print(f"Credas webhook received for check ID {credas_check_id}. Status: {status}")
                    # Log the event
                    # log_integration_event(integration_instance, 'INFO', f'Credas webhook received. Check ID: {credas_check_id}, Status: {status}', related_object=compliance_check)

                    return JsonResponse({'status': 'success', 'message': 'Webhook received and processed'})
                except ComplianceCheck.DoesNotExist:
                    print(f"Credas webhook received for unknown check ID: {credas_check_id}")
                    # Log a warning
                    # log_integration_event(integration_instance, 'WARNING', f'Credas webhook received for unknown check ID: {credas_check_id}')
                    return JsonResponse({'status': 'error', 'message': 'Unknown check ID'}, status=404)
            else:
                 print("Credas webhook received with missing check_id.")
                 # Log a warning
                 # log_integration_event(integration_instance, 'WARNING', 'Credas webhook received with missing check_id in payload.')
                 return JsonResponse({'status': 'error', 'message': 'Missing check_id'}, status=400)

        except json.JSONDecodeError:
            print("Credas webhook received with invalid JSON.")
            # Log an error
            # log_integration_event(integration_instance, 'ERROR', 'Credas webhook received with invalid JSON payload.')
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"An error occurred processing Credas webhook: {e}")
            # Log the error
            # log_integration_event(integration_instance, 'ERROR', f'Error processing Credas webhook: {e}')
            return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)

@csrf_exempt # Be cautious with CSRF exemption - implement proper webhook security
def peps_sanctions_webhook_view(request):
    """Webhook endpoint to receive results from PEPs/Sanctions provider."""
    # Implement webhook verification and processing, similar to Credas webhook
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            # Process the webhook payload
            # Find the relevant ComplianceCheck using the check_id from the payload
            peps_check_id = payload.get('check_id')
            status = payload.get('status') # e.g., 'completed', 'failed'
            result_data = payload.get('result') # Detailed result data

            if peps_check_id:
                try:
                    compliance_check = ComplianceCheck.objects.get(peps_sanctions_check_id=peps_check_id)
                    # Update the compliance check based on the webhook data
                    # Example:
                    # compliance_check.peps_sanctions_status = status
                    # compliance_check.peps_sanctions_result_data = result_data # Store results
                    # Update overall compliance check status if needed
                    # if status == 'completed':
                    #     compliance_check.status = 'requires_review' # Ready for internal review
                    # elif status == 'failed':
                    #      compliance_check.status = 'failed'
                    # compliance_check.save()
                    print(f"PEPs/Sanctions webhook received for check ID {peps_check_id}. Status: {status}")
                     # Log the event
                    # log_integration_event(integration_instance, 'INFO', f'PEPs/Sanctions webhook received. Check ID: {peps_check_id}, Status: {status}', related_object=compliance_check)

                    return JsonResponse({'status': 'success', 'message': 'Webhook received and processed'})
                except ComplianceCheck.DoesNotExist:
                    print(f"PEPs/Sanctions webhook received for unknown check ID: {peps_check_id}")
                     # Log a warning
                    # log_integration_event(integration_instance, 'WARNING', f'PEPs/Sanctions webhook received for unknown check ID: {peps_check_id}')
                    return JsonResponse({'status': 'error', 'message': 'Unknown check ID'}, status=404)
            else:
                 print("PEPs/Sanctions webhook received with missing check_id.")
                 # Log a warning
                 # log_integration_event(integration_instance, 'WARNING', 'PEPs/Sanctions webhook received with missing check_id in payload.')
                 return JsonResponse({'status': 'error', 'message': 'Missing check_id'}, status=400)

        except json.JSONDecodeError:
            print("PEPs/Sanctions webhook received with invalid JSON.")
            # Log an error
            # log_integration_event(integration_instance, 'ERROR', 'PEPs/Sanctions webhook received with invalid JSON payload.')
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"An error occurred processing PEPs/Sanctions webhook: {e}")
            # Log the error
            # log_integration_event(integration_instance, 'ERROR', f'Error processing PEPs/Sanctions webhook: {e}')
            return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)


# Add view for evaluating/completing a compliance check
@login_required
# @notary_required # Only Notaries/Admins can finalize checks
def compliance_check_evaluate_view(request, pk):
    """View to review answers and results and set the final status."""
    compliance_check = get_object_or_404(ComplianceCheck, pk=pk)
    # Permission check: Ensure user can evaluate this check
    # Example: user is admin, or is a notary/solicitor assigned to the matter/client
    # if not (request.user.is_superuser or request.user.role == 'admin' or
    #         (request.user.role in ['notary', 'solicitor'] and
    #          (compliance_check.client and compliance_check.client in request.user.clients.all() or
    #           compliance_check.matter and compliance_check.matter in request.user.matters.all()))):
    #     messages.error(request, "You do not have permission to evaluate this compliance check.")
    #     return redirect('compliance_check_detail', pk=pk)

    # Placeholder for evaluation logic
    if request.method == 'POST':
        # Logic to evaluate answers and external check results
        # Based on evaluation, set the final status (passed/failed/requires_review)
        # Example:
        # if evaluate_compliance_check_logic(compliance_check): # Implement this logic
        #     compliance_check.status = 'passed'
        # else:
        #     compliance_check.status = 'failed'
        # compliance_check.completed_at = datetime.now(timezone.utc) # Need to import datetime, timezone
        # compliance_check.save()
        messages.info(request, f"Compliance check #{compliance_check.pk} evaluation triggered (placeholder).")
        return redirect('compliance_check_detail', pk=pk)

    # For GET request, display evaluation details or a confirmation
    context = {
        'compliance_check': compliance_check,
        # Pass evaluation details to the template
    }
    return render(request, 'compliance/compliance_check_evaluate.html', context) # Needs template


# Add view for generating a compliance report
@login_required
def compliance_check_report_view(request, pk):
    """View to generate and display/download a compliance report."""
    compliance_check = get_object_or_404(ComplianceCheck, pk=pk)
     # Permission check: Ensure user can view report
    # if not (request.user.is_superuser or request.user.role == 'admin' or
    #         compliance_check.initiated_by == request.user or
    #         (compliance_check.client and compliance_check.client in request.user.clients.all() or
    #          compliance_check.matter and compliance_check.matter in request.user.matters.all())):
    #     messages.error(request, "You do not have permission to view this compliance report.")
    #     return redirect('compliance_check_detail', pk=pk)

    # Placeholder for report generation logic
    # Could generate HTML, PDF, etc.
    messages.info(request, f"Compliance report for check #{compliance_check.pk} generated (placeholder).")
    # Call a utility function to generate the report
    # report_content = generate_compliance_report_logic(compliance_check)

    # For now, just redirect back
    return redirect('compliance_check_detail', pk=pk)
