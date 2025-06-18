# apps/dashboard/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required # Require user to be logged in to view the dashboard
def dashboard_view(request):
    """
    Basic placeholder view for the dashboard.
    You'll add more context and logic here later.
    """
    context = {
        'welcome_message': f"Welcome back, {request.user.username}!",
        # Add data for dashboard widgets, summaries, etc.
    }
    return render(request, 'dashboard/dashboard.html', context)

# Add other views for dashboard components as needed
