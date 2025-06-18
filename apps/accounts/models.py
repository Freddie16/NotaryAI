# apps/accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom User Model with roles.
    """
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('paid_user', 'Paid User'),
        ('notary', 'Notary'),
        ('solicitor', 'Solicitor'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='paid_user')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username

    def is_notary(self):
        return self.role == 'notary'

    def is_admin(self):
        return self.role == 'admin'
