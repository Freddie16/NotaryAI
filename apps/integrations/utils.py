# apps/integrations/utils.py
# Utility functions for interacting with external integration services.

import requests # For general HTTP requests (Credas, etc.)
from django.conf import settings
from datetime import datetime, timezone
from .models import Integration, IntegrationLog # Import models
import json # For handling JSON data

# Import specific libraries for integrations (make sure they are in requirements.txt)
# Ensure these packages are installed successfully in your environment
from zoomus import ZoomClient # Example for Zoom

# --- Google API Imports (Replacing Microsoft Graph) ---
from googleapiclient.discovery import build # To build service objects (like Gmail)
from google.oauth2.credentials import Credentials # To handle OAuth tokens
from google_auth_oauthlib.flow import Flow # To handle the OAuth 2.0 flow
from google.auth.transport.requests import Request # For refreshing tokens
from googleapiclient.errors import HttpError # To catch API errors

# --- Logging Utility ---
def log_integration_event(integration_instance, level, message, related_object=None):
    """Logs an event related to an integration."""
    # Ensure integration_instance is an Integration object or None
    if not isinstance(integration_instance, Integration) and integration_instance is not None:
        # Try to get the Integration object if an ID is passed
        if isinstance(integration_instance, int):
             try:
                 integration_instance = Integration.objects.get(pk=integration_instance)
             except Integration.DoesNotExist:
                 integration_instance = None
        else:
            integration_instance = None # Set to None if invalid type

    IntegrationLog.objects.create(
        integration=integration_instance,
        level=level,
        message=message,
        related_object_id=related_object.pk if related_object else None,
        related_object_type=related_object.__class__.__name__ if related_object else None,
    )

# --- Credas Integration (Example) ---
def trigger_credas_check_api(client_data):
    """
    Placeholder function to trigger a Credas check via their API.
    Requires actual Credas API implementation.
    """
    try:
        integration = Integration.objects.get(service_name='credas', is_enabled=True)
        if not integration.api_key:
            log_integration_event(integration, 'ERROR', 'Credas API key is not configured.')
            return False, "Credas API key not configured.", None

        # Replace with actual Credas API endpoint and payload
        credas_api_url = 'https://api.credas.com/v1/checks' # Example URL
        headers = {
            'Authorization': f'Bearer {integration.api_key}',
            'Content-Type': 'application/json',
        }

        # Example payload (structure depends on Credas API)
        payload = {
            'client_info': client_data, # Pass client data dictionary
            # ... other required parameters ...
        }

        response = requests.post(credas_api_url, json=payload, headers=headers)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        result = response.json()
        check_id = result.get('check_id')
        status = result.get('status')

        log_integration_event(integration, 'INFO', f'Credas check initiated. ID: {check_id}, Status: {status}')
        return True, f"Credas check initiated successfully. Status: {status}", check_id

    except Integration.DoesNotExist:
        print("Credas integration is not enabled or configured.")
        # Log this even if the integration object doesn't exist
        # This requires a different logging approach or checking before calling this function
        log_integration_event(None, 'WARNING', 'Attempted to trigger Credas check but integration not found or enabled.')
        return False, "Credas integration not enabled or configured.", None
    except requests.exceptions.RequestException as e:
        print(f"Error triggering Credas check: {e}")
        if 'integration' in locals(): # Check if integration object was retrieved
             log_integration_event(integration, 'ERROR', f'Request failed during Credas check trigger: {e}')
        return False, f"Request failed: {e}", None
    except Exception as e:
        print(f"An unexpected error occurred during Credas check trigger: {e}")
        if 'integration' in locals():
            log_integration_event(integration, 'ERROR', f'Unexpected error during Credas check trigger: {e}')
        return False, f"Unexpected error: {e}", None


def get_credas_check_result_api(check_id):
    """
    Placeholder function to retrieve the result of a Credas check.
    Requires actual Credas API implementation.
    """
    try:
        integration = Integration.objects.get(service_name='credas', is_enabled=True)
        if not integration.api_key:
            log_integration_event(integration, 'ERROR', 'Credas API key is not configured for result retrieval.')
            return False, "Credas API key not configured.", None

        # Replace with actual Credas API endpoint for getting results
        credas_api_url = f'https://api.credas.com/v1/checks/{check_id}' # Example URL
        headers = {
            'Authorization': f'Bearer {integration.api_key}',
            'Content-Type': 'application/json',
        }

        response = requests.get(credas_api_url, headers=headers)
        response.raise_for_status()

        result = response.json()
        log_integration_event(integration, 'INFO', f'Credas check result retrieved for ID: {check_id}')
        return True, "Credas result retrieved successfully.", result

    except Integration.DoesNotExist:
        print("Credas integration is not enabled or configured.")
        log_integration_event(None, 'WARNING', 'Attempted to get Credas result but integration not found or enabled.')
        return False, "Credas integration not enabled or configured.", None
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving Credas check result: {e}")
        if 'integration' in locals():
            log_integration_event(integration, 'ERROR', f'Request failed during Credas result retrieval: {e}')
        return False, f"Request failed: {e}", None
    except Exception as e:
        print(f"An unexpected error occurred while retrieving Credas result: {e}")
        if 'integration' in locals():
            log_integration_event(integration, 'ERROR', f'Unexpected error during Credas result retrieval: {e}')
        return False, f"Unexpected error: {e}", None


# --- Zoom Integration (Example) ---
def get_zoom_client():
    """Helper to get a configured ZoomClient instance."""
    try:
        integration = Integration.objects.get(service_name='zoom', is_enabled=True)
        if not integration.api_key or not integration.api_secret:
             log_integration_event(integration, 'ERROR', 'Zoom API Key or Secret is not configured.')
             return None

        # Zoom API uses JWT or OAuth. This example assumes JWT for simplicity.
        # For OAuth, you'd need to handle token refresh.
        # Replace with appropriate client initialization based on Zoom SDK and auth method
        client = ZoomClient(integration.api_key, integration.api_secret)
        # Attach the integration instance to the client for logging purposes (optional)
        client._integration_instance = integration
        return client

    except Integration.DoesNotExist:
        print("Zoom integration is not enabled or configured.")
        log_integration_event(None, 'WARNING', 'Attempted to get Zoom client but integration not found or enabled.')
        return None
    except Exception as e:
        print(f"Error initializing Zoom client: {e}")
        if 'integration' in locals():
            log_integration_event(integration, 'ERROR', f'Error initializing Zoom client: {e}')
        return False, f"Error initializing client: {e}", None


def create_zoom_meeting_api(topic, start_time, duration_minutes, agenda=None):
    """
    Placeholder function to create a Zoom meeting.
    Requires actual Zoom API implementation using zoomus or requests.
    """
    client = get_zoom_client()
    if not client:
        return False, "Zoom integration not configured.", None

    try:
        # Replace with actual Zoom API call using the client
        # Example using zoomus (API method names might vary)
        # response = client.meeting.create(
        #     user_id='me', # Or the user ID of the host
        #     topic=topic,
        #     start_time=start_time.isoformat(), # Needs to be in ISO 8601 format
        #     duration=duration_minutes,
        #     agenda=agenda,
        #     type=2, # Scheduled meeting
        # )
        # meeting_data = response.json()
        # join_url = meeting_data.get('join_url')
        # meeting_id = meeting_data.get('id')

        # Placeholder success response
        join_url = "https://zoom.us/j/1234567890" # Example
        meeting_id = "1234567890" # Example

        log_integration_event(client._integration_instance, 'INFO', f'Zoom meeting created. ID: {meeting_id}') # Assuming client has access to integration instance
        return True, "Zoom meeting created successfully.", {'join_url': join_url, 'meeting_id': meeting_id}

    except Exception as e:
        print(f"Error creating Zoom meeting: {e}")
        if 'client' in locals() and hasattr(client, '_integration_instance'):
             log_integration_event(client._integration_instance, 'ERROR', f'Error creating Zoom meeting: {e}')
        return False, f"Error creating meeting: {e}", None


# --- Google API Integration (Gmail) (Replacing Microsoft Graph) ---

def get_google_credentials(integration_instance):
    """
    Retrieves and refreshes Google OAuth credentials for an integration instance.
    """
    if not integration_instance or integration_instance.service_name != 'gmail' or not integration_instance.google_refresh_token:
        log_integration_event(integration_instance, 'WARNING', 'Gmail integration not configured or refresh token missing.')
        return None

    creds = Credentials(
        token=integration_instance.google_access_token,
        refresh_token=integration_instance.google_refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
        scopes=integration_instance.google_token_scope.split(',') if integration_instance.google_token_scope else [],
        # Set expiry from stored datetime
        expiry=integration_instance.google_token_expires_at
    )

    # Check if the access token is expired and needs refreshing
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Save the new tokens back to the Integration model
            integration_instance.google_access_token = creds.token
            integration_instance.google_token_expires_at = creds.expiry
            # Only update refresh token if it changed (usually doesn't)
            if creds.refresh_token and creds.refresh_token != integration_instance.google_refresh_token:
                 integration_instance.google_refresh_token = creds.refresh_token
            integration_instance.save()
            log_integration_event(integration_instance, 'INFO', 'Google access token refreshed successfully.')
        except Exception as e:
            log_integration_event(integration_instance, 'ERROR', f'Error refreshing Google access token: {e}')
            return None
    elif creds.expired and not creds.refresh_token:
         log_integration_event(integration_instance, 'ERROR', 'Google access token expired and no refresh token available.')
         return None

    return creds


def get_gmail_service(integration_instance):
    """Helper to get an authenticated Google Gmail service object."""
    creds = get_google_credentials(integration_instance)
    if not creds:
        return None

    try:
        # Build the Gmail service object
        service = build('gmail', 'v1', credentials=creds)
        # Attach the integration instance to the service object for logging (optional)
        service._integration_instance = integration_instance
        return service
    except Exception as e:
        log_integration_event(integration_instance, 'ERROR', f'Error building Gmail service: {e}')
        return None


def send_gmail_email_api(integration_instance, to_recipients, subject, body_html):
    """
    Sends an email via the Google Gmail API.
    to_recipients should be a list of email addresses.
    """
    service = get_gmail_service(integration_instance)
    if not service:
        return False, "Gmail integration not configured or authenticated.", None

    try:
        # Create the email message
        import base64
        from email.mime.text import MIMEText

        message = MIMEText(body_html, 'html')
        message['to'] = ", ".join(to_recipients)
        message['subject'] = subject
        # message['from'] = 'me' # Gmail API sends from the authenticated user's address

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw_message}

        # Send the email
        # The 'me' user ID refers to the authenticated user
        sent_message = service.users().messages().send(userId='me', body=body).execute()

        message_id = sent_message.get('id')
        log_integration_event(integration_instance, 'INFO', f'Gmail email sent successfully. Message ID: {message_id}')
        return True, "Email sent successfully.", {'message_id': message_id}

    except HttpError as e:
        log_integration_event(integration_instance, 'ERROR', f'Gmail API error sending email: {e}')
        print(f"Gmail API error sending email: {e}")
        return False, f"Gmail API error: {e}", None
    except Exception as e:
        log_integration_event(integration_instance, 'ERROR', f'An unexpected error occurred sending Gmail email: {e}')
        print(f"An unexpected error occurred sending Gmail email: {e}")
        return False, f"Unexpected error: {e}", None

# --- PEPs and Sanctions Integration (Example) ---
def trigger_peps_sanctions_check_api(client_data):
    """
    Placeholder function to trigger a PEPs and Sanctions check via an external API.
    Requires actual API implementation.
    """
    try:
        integration = Integration.objects.get(service_name='peps_sanctions', is_enabled=True)
        if not integration.api_key:
            log_integration_event(integration, 'ERROR', 'PEPs/Sanctions API key is not configured.')
            return False, "PEPs/Sanctions API key not configured.", None

        # Replace with actual PEPs/Sanctions API endpoint and payload
        peps_api_url = 'https://api.pepssanctions.com/v1/checks' # Example URL
        headers = {
            'Authorization': f'Bearer {integration.api_key}',
            'Content-Type': 'application/json',
        }

        # Example payload (structure depends on the API)
        payload = {
            'client_info': client_data, # Pass client data dictionary
            # ... other required parameters ...
        }

        response = requests.post(peps_api_url, json=payload, headers=headers)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        result = response.json()
        check_id = result.get('check_id')
        status = result.get('status')

        log_integration_event(integration, 'INFO', f'PEPs/Sanctions check initiated. ID: {check_id}, Status: {status}')
        return True, f"PEPs/Sanctions check initiated successfully. Status: {status}", check_id

    except Integration.DoesNotExist:
        print("PEPs/Sanctions integration is not enabled or configured.")
        log_integration_event(None, 'WARNING', 'Attempted to trigger PEPs/Sanctions check but integration not found or enabled.')
        return False, "PEPs/Sanctions integration not enabled or configured.", None
    except requests.exceptions.RequestException as e:
        print(f"Error triggering PEPs/Sanctions check: {e}")
        if 'integration' in locals(): # Check if integration object was retrieved
             log_integration_event(integration, 'ERROR', f'Request failed during PEPs/Sanctions check trigger: {e}')
        return False, f"Request failed: {e}", None
    except Exception as e:
        print(f"An unexpected error occurred during PEPs/Sanctions check trigger: {e}")
        if 'integration' in locals():
            log_integration_event(integration, 'ERROR', f'Unexpected error during PEPs/Sanctions check trigger: {e}')
        return False, f"Unexpected error: {e}", None


def get_peps_sanctions_check_result_api(check_id):
    """
    Placeholder function to retrieve the result of a PEPs and Sanctions check.
    Requires actual API implementation.
    """
    try:
        integration = Integration.objects.get(service_name='peps_sanctions', is_enabled=True)
        if not integration.api_key:
            log_integration_event(integration, 'ERROR', 'PEPs/Sanctions API key is not configured for result retrieval.')
            return False, "PEPs/Sanctions API key not configured.", None

        # Replace with actual PEPs/Sanctions API endpoint for getting results
        peps_api_url = f'https://api.pepssanctions.com/v1/checks/{check_id}' # Example URL
        headers = {
            'Authorization': f'Bearer {integration.api_key}',
            'Content-Type': 'application/json',
        }

        response = requests.get(peps_api_url, headers=headers)
        response.raise_for_status()

        result = response.json()
        log_integration_event(integration, 'INFO', f'PEPs/Sanctions check result retrieved for ID: {check_id}')
        return True, "PEPs/Sanctions result retrieved successfully.", result

    except Integration.DoesNotExist:
        print("PEPs/Sanctions integration is not enabled or configured.")
        log_integration_event(None, 'WARNING', 'Attempted to get PEPs/Sanctions result but integration not found or enabled.')
        return False, "PEPs/Sanctions integration not enabled or configured.", None
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving PEPs/Sanctions check result: {e}")
        if 'integration' in locals():
            log_integration_event(integration, 'ERROR', f'Request failed during PEPs/Sanctions result retrieval: {e}')
        return False, f"Request failed: {e}", None
    except Exception as e:
        print(f"An unexpected error occurred while retrieving PEPs/Sanctions result: {e}")
        if 'integration' in locals():
            log_integration_event(integration, 'ERROR', f'Unexpected error during PEPs/Sanctions result retrieval: {e}')
        return False, f"Unexpected error: {e}", None


# Add placeholder functions for other integration actions (e.g., Zoom meeting update/delete, Outlook calendar events, mobile camera upload handling)

# --- Generic Integration Test ---
def test_integration_connection(integration_instance):
    """
    Tests the connection for a given integration service.
    Requires specific test logic for each service.
    """
    if integration_instance.service_name == 'credas':
        # Test Credas connection (e.g., a simple ping endpoint or a basic lookup)
        # This requires knowing the Credas API test method
        print("Placeholder: Testing Credas connection...")
        # success, message, _ = trigger_credas_check_api({'test': True}) # Example using trigger function (might not be suitable)
        # return success, message
        return False, "Credas test not implemented." # Placeholder

    elif integration_instance.service_name == 'peps_sanctions':
         # Test PEPs/Sanctions connection (e.g., a simple ping endpoint or a basic lookup)
         print("Placeholder: Testing PEPs/Sanctions connection...")
         # success, message, _ = trigger_peps_sanctions_check_api({'test': True}) # Example
         # return success, message
         return False, "PEPs/Sanctions test not implemented." # Placeholder

    elif integration_instance.service_name == 'zoom':
        # Test Zoom connection (e.g., get user info)
        client = get_zoom_client()
        if client:
            try:
                # response = client.user.me() # Example using zoomus
                # if response.status_code == 200:
                #     return True, "Zoom connection successful."
                # else:
                #     return False, f"Zoom connection failed: Status {response.status_code}"
                 print("Placeholder: Testing Zoom connection...")
                 return False, "Zoom test not implemented." # Placeholder
            except Exception as e:
                return False, f"Zoom connection test error: {e}"
        else:
            return False, "Zoom client not initialized."

    elif integration_instance.service_name == 'gmail': # Changed from 'outlook' to 'gmail'
        # Test Gmail connection (e.g., get user profile)
        service = get_gmail_service(integration_instance)
        if service:
            try:
                # Attempt to get user profile info
                profile = service.users().getProfile(userId='me').execute()
                email_address = profile.get('emailAddress')
                if email_address:
                    log_integration_event(integration_instance, 'INFO', f'Gmail connection test successful for {email_address}.')
                    return True, f"Gmail connection successful for {email_address}."
                else:
                    log_integration_event(integration_instance, 'ERROR', 'Gmail connection test failed: Could not retrieve email address.')
                    return False, "Gmail connection failed: Could not retrieve email address."
            except HttpError as e:
                log_integration_event(integration_instance, 'ERROR', f'Gmail API error during connection test: {e}')
                return False, f"Gmail API error during test: {e}"
            except Exception as e:
                log_integration_event(integration_instance, 'ERROR', f'An unexpected error occurred during Gmail connection test: {e}')
                return False, f"Unexpected error during Gmail test: {e}"
        else:
            return False, "Gmail client not initialized or authenticated."

    else:
        return False, "Unknown integration service."
