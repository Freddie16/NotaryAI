# apps/workflows/utils.py
# Utility functions for workflow and matter management, including AI integration.

import google.generativeai as genai
from django.conf import settings
import json

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in settings. Gemini AI features will not be available.")
    genai = None

def generate_workflow_steps_ai(matter_title, matter_description):
    """
    Uses Gemini AI to generate a list of suggested workflow steps for a matter.
    """
    if not genai:
        print("Gemini AI is not configured. Cannot generate workflow steps.")
        return None
    if not matter_title and not matter_description:
        print("No matter title or description provided for workflow step generation.")
        return None

    prompt = f"""
Based on the following notarial matter title and description, suggest a sequence of logical workflow steps.
Each step should be a concise action or task.
Return the steps as a JSON array of strings.

Matter Title: {matter_title}
Matter Description: {matter_description or 'N/A'}

JSON Workflow Steps:
"""

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        try:
            json_string = response.text.strip()
            if json_string.startswith('[') and json_string.endswith(']'):
                 steps = json.loads(json_string)
                 if isinstance(steps, list):
                     return steps
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
        print(f"Error generating workflow steps with Gemini AI: {e}")
        return None

def create_workflow_from_template(matter_instance, template_instance):
    """Creates a Workflow and WorkflowStep objects from a template."""
    pass

def update_matter_status(matter_instance):
    """Updates matter status based on workflow/step statuses."""
    pass
