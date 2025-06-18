# apps/compliance/utils.py
# Utility functions for compliance checks and third-party integrations.

import requests  # You'll need to install the 'requests' library (add to requirements.txt)
from django.conf import settings
from .models import ComplianceCheck  # Import ComplianceCheck model

# Placeholder functions for integrating with third-party services

def trigger_credas_check(client_instance):
    """
    Triggers a Credas identity verification check for a given client.
    Requires Credas API credentials and understanding of their API.
    """
    if not settings.CREDAS_API_KEY:
        print("CREDAS_API_KEY not configured.")
        return False, "Credas API key not configured.", None

    credas_api_url = 'https://api.credas.com/v1/checks'
    headers = {
        'Authorization': f'Bearer {settings.CREDAS_API_KEY}',
        'Content-Type': 'application/json',
    }

    payload = {
        'client_id': client_instance.pk,
        'first_name': client_instance.first_name,
        'last_name': client_instance.last_name,
        'date_of_birth': str(client_instance.date_of_birth),
    }

    try:
        response = requests.post(credas_api_url, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        credas_check_id = result.get('check_id')
        status = result.get('status')

        return True, f"Credas check initiated successfully. Status: {status}", credas_check_id

    except requests.exceptions.RequestException as e:
        print(f"Error triggering Credas check: {e}")
        return False, f"Request failed: {e}", None
    except Exception as e:
        print(f"An unexpected error occurred during Credas check trigger: {e}")
        return False, f"Unexpected error: {e}", None


def get_credas_check_result(check_id):
    """
    Retrieves the result of a Credas check using its ID.
    Requires Credas API.
    """
    if not settings.CREDAS_API_KEY:
        print("CREDAS_API_KEY not configured.")
        return False, "Credas API key not configured.", None

    credas_api_url = f'https://api.credas.com/v1/checks/{check_id}'
    headers = {
        'Authorization': f'Bearer {settings.CREDAS_API_KEY}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.get(credas_api_url, headers=headers)
        response.raise_for_status()

        result = response.json()
        return True, "Credas result retrieved successfully.", result

    except requests.exceptions.RequestException as e:
        print(f"Error retrieving Credas check result: {e}")
        return False, f"Request failed: {e}", None
    except Exception as e:
        print(f"An unexpected error occurred while retrieving Credas result: {e}")
        return False, f"Unexpected error: {e}", None


def trigger_peps_sanctions_check(client_instance):
    """
    Triggers a PEPs and sanctions check for a given client.
    Requires integration with a PEPs/Sanctions data provider API.
    """
    if not settings.PEPS_SANCTIONS_API_KEY:
        print("PEPS_SANCTIONS_API_KEY not configured.")
        return False, "PEPs/Sanctions API key not configured.", None

    peps_api_url = 'https://api.peps-sanctions-provider.com/v1/search'
    headers = {
        'Authorization': f'Bearer {settings.PEPS_SANCTIONS_API_KEY}',
        'Content-Type': 'application/json',
    }

    payload = {
        'client_id': client_instance.pk,
        'name': f"{client_instance.first_name} {client_instance.last_name}",
        'date_of_birth': str(client_instance.date_of_birth),
    }

    try:
        response = requests.post(peps_api_url, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        check_id = result.get('search_id')
        match_found = result.get('match_found', False)

        return True, f"PEPs/Sanctions check initiated. Match found: {match_found}", check_id

    except requests.exceptions.RequestException as e:
        print(f"Error triggering PEPs/Sanctions check: {e}")
        return False, f"Request failed: {e}", None
    except Exception as e:
        print(f"An unexpected error occurred during PEPs/Sanctions check trigger: {e}")
        return False, f"Unexpected error: {e}", None


def get_peps_sanctions_check_result(check_id):
    """
    Retrieves the result of a PEPs/Sanctions check using its ID.
    Requires integration with a PEPs/Sanctions data provider API.
    """
    if not settings.PEPS_SANCTIONS_API_KEY:
        print("PEPS_SANCTIONS_API_KEY not configured.")
        return False, "PEPs/Sanctions API key not configured.", None

    peps_api_url = f'https://api.peps-sanctions-provider.com/v1/search/{check_id}'
    headers = {
        'Authorization': f'Bearer {settings.PEPS_SANCTIONS_API_KEY}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.get(peps_api_url, headers=headers)
        response.raise_for_status()

        result = response.json()
        return True, "PEPs/Sanctions result retrieved successfully.", result

    except requests.exceptions.RequestException as e:
        print(f"Error retrieving PEPs/Sanctions check result: {e}")
        return False, f"Request failed: {e}", None
    except Exception as e:
        print(f"An unexpected error occurred while retrieving PEPs/Sanctions result: {e}")
        return False, f"Unexpected error: {e}", None


# Add placeholder functions for other compliance-related utilities
# def evaluate_compliance_check(compliance_check_instance):
#     """Evaluates the answers and external check results for a compliance check."""
#     pass
