# apps/accounts/utils.py
# Placeholder for any utility functions related to the accounts app.

# Example: A decorator to restrict views based on user role
from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    """Checks if the user has the 'admin' role."""
    return user.is_authenticated and user.role == 'admin'

def is_notary(user):
    """Checks if the user has the 'notary' role."""
    return user.is_authenticated and user.role == 'notary'

def is_solicitor(user):
    """Checks if the user has the 'solicitor' role."""
    return user.is_authenticated and user.role == 'solicitor'

def is_paid_user(user):
    """Checks if the user has the 'paid_user' role."""
    return user.is_authenticated and user.role == 'paid_user'

# Decorators for views
admin_required = user_passes_test(is_admin)
notary_required = user_passes_test(is_notary)
solicitor_required = user_passes_test(is_solicitor)
paid_user_required = user_passes_test(is_paid_user)

# You can combine decorators for multiple roles if needed
def is_notary_or_solicitor(user):
     return is_notary(user) or is_solicitor(user)
     notary_or_solicitor_required = user_passes_test(is_notary_or_solicitor)

