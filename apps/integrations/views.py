# apps/integrations/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse, HttpResponse # Import HttpResponse
from django.views.decorators.csrf import csrf_exempt # Needed for webhooks

from .models import Integration, IntegrationLog
from .forms import IntegrationForm
# Import utility functions
from .utils import (
    test_integration_connection,
    log_integration_event,
    trigger_credas_check_api,
    trigger_peps_sanctions_check_api,
    send_gmail_email_api # Import the new Gmail utility function
    # Import other utility functions as needed
)

# Import Google OAuth related libraries
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import json # Needed for webhook processing and potentially OAuth state
import os # Needed for client_secrets.json (or equivalent)

# Define the scopes required for Gmail access
# https://developers.google.com/gmail/api/auth/scopes
GOOGLE_EMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/userinfo.email'] # Add other scopes if needed (e.g., read)

# Helper function to build the Google OAuth flow
def get_google_oauth_flow(request):
    """Builds the Google OAuth 2.0 flow object."""
    # In a real application, you would load client secrets from a file
    # or configuration. For simplicity, we'll use settings.
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI],
            # Add any other necessary fields from your client_secrets.json
        }
    }

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=GOOGLE_EMAIL_SCOPES,
        redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI
    )
    return flow


@login_required
# @admin_required # Example: Only Admins can manage integrations
def integration_list_view(request):
    """
    View to list all configured integrations.
    """
    integrations = Integration.objects.all()
    context = {
        'integrations': integrations,
    }
    return render(request, 'integrations/integration_list.html', context)

@login_required
# @admin_required # Example: Only Admins can create integrations
def integration_create_view(request):
    """
    View to create a new integration configuration.
    """
    if request.method == 'POST':
        form = IntegrationForm(request.POST)
        if form.is_valid():
            integration = form.save()
            messages.success(request, f'Integration "{integration.get_service_name_display()}" created successfully.')
            return redirect('integration_list')
    else:
        form = IntegrationForm()

    context = {
        'form': form,
    }
    return render(request, 'integrations/integration_create.html', context)

@login_required
# @admin_required # Example: Only Admins can configure integrations
def integration_config_view(request, pk):
    """
    View to configure an existing integration.
    Includes options for API keys and initiating OAuth flows.
    """
    integration = get_object_or_404(Integration, pk=pk)

    if request.method == 'POST':
        form = IntegrationForm(request.POST, instance=integration)
        if form.is_valid():
            form.save()
            messages.success(request, f'Integration "{integration.get_service_name_display()}" configured successfully.')
            return redirect('integration_list')
    else:
        form = IntegrationForm(instance=integration)

    context = {
        'integration': integration,
        'form': form,
        'google_oauth_redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI, # Pass redirect URI for display
    }
    return render(request, 'integrations/integration_config.html', context)

@login_required
# @admin_required # Example: Only Admins can delete integrations
def integration_delete_view(request, pk):
    """
    View to delete an integration configuration.
    """
    integration = get_object_or_404(Integration, pk=pk)

    if request.method == 'POST':
        service_name = integration.get_service_name_display()
        integration.delete()
        messages.success(request, f'Integration "{service_name}" deleted successfully.')
        return redirect('integration_list')

    context = {
        'integration': integration,
    }
    return render(request, 'integrations/integration_confirm_delete.html', context)


@login_required
# @admin_required # Example: Only Admins can test integrations
def integration_test_view(request, pk):
    """
    View to test the connection for a specific integration.
    """
    integration = get_object_or_404(Integration, pk=pk)

    # Perform the test using the utility function
    success, message = test_integration_connection(integration)

    if success:
        messages.success(request, f'Connection test for "{integration.get_service_name_display()}" successful: {message}')
    else:
        messages.error(request, f'Connection test for "{integration.get_service_name_display()}" failed: {message}')

    return redirect('integration_config', pk=pk) # Redirect back to config page


# --- Google OAuth 2.0 Flow Views (Replacing Microsoft Graph) ---

@login_required
# @admin_required # Example: Only Admins can initiate Google OAuth
def google_oauth_initiate_view(request, pk):
    """
    Initiates the Google OAuth 2.0 flow for a specific Gmail integration.
    """
    integration = get_object_or_404(Integration, pk=pk, service_name='gmail')

    flow = get_google_oauth_flow(request)

    # Store the integration ID in the session to retrieve it in the callback
    request.session['google_oauth_integration_id'] = integration.pk

    # Generate the authorization URL
    # access_type offline is crucial to get a refresh token
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true' # Request to include scopes already granted
    )

    # Store the state in the session for security (CSRF protection)
    request.session['google_oauth_state'] = state

    # Redirect the user to Google's authorization page
    return redirect(authorization_url)


@login_required
# @admin_required # Example: Only Admins can handle Google OAuth callback
def google_oauth_callback_view(request):
    """
    Handles the callback from Google after the user grants authorization.
    Exchanges the authorization code for access and refresh tokens.
    """
    # Retrieve the state from the session and compare it to the state parameter
    state = request.session.pop('google_oauth_state', None)
    if not state or state != request.GET.get('state'):
        messages.error(request, 'Invalid OAuth state. Possible CSRF attack.')
        log_integration_event(None, 'ERROR', 'Invalid Google OAuth state received.')
        return redirect('integration_list') # Redirect to a safe page

    # Retrieve the integration ID from the session
    integration_id = request.session.pop('google_oauth_integration_id', None)
    if not integration_id:
        messages.error(request, 'OAuth flow interrupted. Integration ID missing from session.')
        log_integration_event(None, 'ERROR', 'Google OAuth callback: Integration ID missing from session.')
        return redirect('integration_list')

    try:
        integration = Integration.objects.get(pk=integration_id, service_name='gmail')
    except Integration.DoesNotExist:
        messages.error(request, 'Invalid integration ID in session.')
        log_integration_event(None, 'ERROR', f'Google OAuth callback: Integration with ID {integration_id} not found.')
        return redirect('integration_list')


    flow = get_google_oauth_flow(request)

    # Exchange the authorization code for credentials (tokens)
    try:
        # Fetch the access and refresh tokens
        flow.fetch_token(authorization_response=request.build_absolute_uri())

        # Get the credentials object
        creds = flow.credentials

        # Store the credentials in the Integration model
        integration.google_access_token = creds.token
        integration.google_refresh_token = creds.refresh_token # Store refresh token for offline access
        integration.google_token_expires_at = creds.expiry
        integration.google_token_scope = ",".join(creds.scopes) if creds.scopes else "" # Store scopes

        # Enable the integration if it was disabled
        integration.is_enabled = True
        integration.save()

        messages.success(request, f'Google account linked successfully for {integration.get_service_name_display()} integration.')
        log_integration_event(integration, 'INFO', 'Google account linked successfully via OAuth.')

    except Exception as e:
        messages.error(request, f'Error during Google OAuth callback: {e}')
        log_integration_event(integration, 'ERROR', f'Error during Google OAuth callback: {e}')


    # Redirect back to the integration config page
    return redirect('integration_config', pk=integration.pk)


# --- Webhook Views (Keeping Credas and PEPs/Sanctions) ---
# These are typically API endpoints, often exempted from CSRF (with caution!)
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

# Add placeholder views for other integration actions (e.g., mobile camera upload handling)
# @csrf_exempt # Example for API endpoint
# def mobile_document_upload_api(request):
#     """API endpoint for mobile document uploads."""
#     pass # Implementation needed

