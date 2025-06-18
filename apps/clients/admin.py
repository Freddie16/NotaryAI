from django.contrib import admin
from .models import Client, Lead

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'client_type', 'email', 'phone_number', 'status', 'created_at', 'created_by')
    list_filter = ('client_type', 'status', 'created_at')
    search_fields = ('first_name', 'last_name', 'business_name', 'email', 'phone_number', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'segmentation_tags')
    fieldsets = (
        (None, {'fields': ('client_type', 'status', 'notes')}),
        ('Individual Details', {'fields': ('first_name', 'last_name', 'date_of_birth'), 'classes': ('collapse',)}),
        ('Business Details', {'fields': ('business_name', 'registration_number'), 'classes': ('collapse',)}),
        ('Contact Information', {'fields': ('email', 'phone_number', 'address')}),
        ('System Information', {'fields': ('created_by', 'created_at', 'updated_at', 'segmentation_tags')}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'status', 'created_at', 'assigned_to')
    list_filter = ('status', 'created_at', 'assigned_to')
    search_fields = ('name', 'email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('name', 'status', 'notes', 'assigned_to')}),
        ('Contact Information', {'fields': ('email', 'phone_number')}),
        ('System Information', {'fields': ('source', 'created_at', 'updated_at')}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
