# apps/integrations/admin.py

from django.contrib import admin
from .models import Integration, IntegrationLog

# Custom Admin for Integration model
class IntegrationAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = (
        'service_name',
        'is_enabled',
        # Removed 'configured_by', 'configured_at', 'last_tested_at', 'test_status'
        # as they are not currently fields on the model or need custom handling.
        # You can add custom methods here if you want to display related info.
        # Example: 'get_configured_by', 'get_last_tested_status'
    )

    # Fields to use for filtering in the list view
    list_filter = (
        'is_enabled',
        'service_name',
        # Removed 'test_status' as it's not a field.
        # You might add custom list filters later if needed.
    )

    # Fields to search by in the list view
    search_fields = (
        'service_name',
        'api_key', # Be cautious searching API keys in a real system
        # Add search fields for OAuth credentials if necessary (with caution)
        # 'google_access_token',
        # 'google_refresh_token',
    )

    # Fields to make read-only in the detail view
    # These are typically fields set automatically or via the OAuth flow.
    # Removed fields that were removed/renamed in the model.
    readonly_fields = (
        # 'configured_by', # Removed
        # 'configured_at', # Removed
        # 'last_tested_at', # Removed
        # 'test_status', # Removed
        'google_access_token', # Renamed from access_token
        'google_refresh_token', # Renamed from refresh_token
        'google_token_expires_at', # Renamed from token_expires_at
        'google_token_scope', # New field for Google scopes
    )

    # Fields to group in the detail view (optional)
    fieldsets = (
        (None, {
            'fields': ('service_name', 'is_enabled')
        }),
        ('API Credentials (if applicable)', {
            'fields': ('api_key', 'api_secret'),
            'classes': ('collapse',), # Optional: Collapse this section by default
        }),
        ('Google OAuth Credentials (managed via OAuth flow)', {
            'fields': ('google_access_token', 'google_refresh_token', 'google_token_expires_at', 'google_token_scope'),
            'classes': ('collapse',), # Optional: Collapse this section by default
            'description': 'These fields are populated automatically after a successful Google OAuth flow.',
        }),
        # Add other fieldsets for service-specific configurations
    )

    # You can add custom methods to display information in list_display
    # def get_configured_by(self, obj):
    #     return obj.configured_by.username if obj.configured_by else '-'
    # get_configured_by.short_description = 'Configured By' # Column header

    # def get_last_tested_status(self, obj):
    #     # Implement logic to show last test status based on logs or a field
    #     return "Status Placeholder"
    # get_last_tested_status.short_description = 'Last Test Status'


# Custom Admin for IntegrationLog model
class IntegrationLogAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp',
        'integration',
        'level',
        'message',
        'related_object_type',
        'related_object_id',
    )
    list_filter = (
        'level',
        'integration__service_name', # Filter by integration service name
        'related_object_type',
    )
    search_fields = (
        'message',
        'integration__service_name',
        'related_object_type',
    )
    readonly_fields = (
        'timestamp',
        'integration',
        'level',
        'message',
        'related_object_type',
        'related_object_id',
    )

# Register your models with the custom admin classes
admin.site.register(Integration, IntegrationAdmin)
admin.site.register(IntegrationLog, IntegrationLogAdmin)
