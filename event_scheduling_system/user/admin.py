from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Organizer, Customer


class OrganizerAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization_name')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'organization_name')


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')

# Register the models
admin.site.register(Organizer, OrganizerAdmin)
admin.site.register(Customer, CustomerAdmin)
