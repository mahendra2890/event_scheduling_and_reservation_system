from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Admin configuration for Event model.
    """
    list_display = [
        'title', 'creator', 'start_time', 'end_time', 
        'capacity', 'available_slots', 'created_at'
    ]
    list_filter = [
        'start_time', 'end_time', 'created_at', 'creator'
    ]
    search_fields = ['title', 'description', 'creator__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'capacity')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time')
        }),
        ('Creator', {
            'fields': ('creator',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def available_slots(self, obj):
        """Display available slots in admin."""
        return obj.available_slots
    available_slots.short_description = 'Available Slots'
