# apps/dashboard/models.py

from django.db import models
from django.conf import settings

# You might define models related to dashboard data or configurations here later.
# For example:
# class DashboardWidget(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     widget_type = models.CharField(max_length=100)
#     configuration = models.JSONField(blank=True, null=True)
#     order = models.PositiveIntegerField(default=0)

#     def __str__(self):
#         return f"{self.user.username}'s {self.widget_type} Widget"

#     class Meta:
#         ordering = ['order']
#         unique_together = [['user', 'order']] # Ensure unique order per user

