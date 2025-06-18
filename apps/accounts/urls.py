# apps/accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views # Django's built-in auth views
from . import views
# Import the CustomAuthenticationForm directly from the forms module
from .forms import CustomAuthenticationForm # <-- Added this import

urlpatterns = [
    # URL pattern for user registration
    path('register/', views.register_view, name='register'),

    # URL pattern for user login using Django's built-in view
    # We use a custom form (CustomAuthenticationForm)
    # Pass the imported CustomAuthenticationForm class directly
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html', authentication_form=CustomAuthenticationForm), name='login'), # <-- Updated this line

    # URL pattern for user logout using Django's built-in view
    # Redirect to homepage after logout (or LOGIN_URL)
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # Add other account-related URL patterns here as needed
    # Commented out the profile URL pattern as the view is not yet implemented
    # path('profile/', views.profile_view, name='profile'),
    # path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    # path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    # path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    # path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    # path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
