from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'attendee', 'event', 'status', 'booking_date']
    list_filter = ['status', 'booking_date']
    search_fields = ['attendee__user__username', 'event__title']
    ordering = ['-booking_date']
