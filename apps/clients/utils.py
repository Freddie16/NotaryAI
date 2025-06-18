# apps/clients/utils.py
# Utility functions for client management and AI integration.

import google.generativeai as genai
from django.conf import settings
import json  # To handle JSON data for segmentation tags

# Configure Gemini AI with the API key from settings
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in settings. Gemini AI features will not be available.")
    genai = None  # Set genai to None if API key is missing

def generate_segmentation_tags(client_instance):
    """
    Uses Gemini AI to generate segmentation tags based on client data.
    """
    if not genai:
        print("Gemini AI is not configured. Cannot generate segmentation tags.")
        return None
    if not client_instance:
        print("No client instance provided for segmentation.")
        return None

    # Construct a prompt using relevant client data
    client_data_string = f"""
    Client Type: {client_instance.get_client_type_display()}
    Name: {client_instance.__str__()}
    Email: {client_instance.email or 'N/A'}
    Phone: {client_instance.phone_number or 'N/A'}
    Address: {client_instance.address or 'N/A'}
    Status: {client_instance.get_status_display()}
    Notes: {client_instance.notes or 'N/A'}
    """
    # Add business specific details if applicable
    if client_instance.client_type == 'business':
        client_data_string += f"""
        Business Name: {client_instance.business_name or 'N/A'}
        Registration Number: {client_instance.registration_number or 'N/A'}
        """
    # Add individual specific details if applicable
    elif client_instance.client_type == 'individual':
        client_data_string += f"""
        Date of Birth: {client_instance.date_of_birth or 'N/A'}
        """

    prompt = f"""
Analyze the following client information and generate a list of relevant segmentation tags (keywords or short phrases).
The tags should help categorize the client for marketing, compliance, or service purposes.
Examples: "High Net Worth", "Small Business", "International Client", "Real Estate", "Estate Planning", "First-Time Client".
Return the tags as a JSON array of strings.

Client Information:
{client_data_string}

JSON Tags:
"""

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        try:
            json_string = response.text.strip()
            if json_string.startswith('[') and json_string.endswith(']'):
                tags = json.loads(json_string)
                if isinstance(tags, list):
                    return tags
                else:
                    print("AI response was not a JSON list.")
                    return None
            else:
                print("AI response did not start/end with JSON array markers.")
                return None

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from AI response: {e}")
            print(f"AI Response Text: {response.text}")
            return None

    except Exception as e:
        print(f"Error generating segmentation tags with Gemini AI: {e}")
        return None

# Add other client-related utility functions here
def convert_lead_to_client(lead_instance):
#     """Converts a Lead instance to a Client instance."""
    pass  # Implementation needed
