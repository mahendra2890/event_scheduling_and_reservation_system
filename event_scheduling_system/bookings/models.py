from django.db import models
from django.utils import timezone
from events.models import Event
from user.models import Customer


class Booking(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    attendee = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='bookings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    class Meta:
        indexes = [
            models.Index(fields=['attendee']),
            models.Index(fields=['event']),
            models.Index(fields=['status']),
        ]
        unique_together = [('attendee', 'event')]
        ordering = ['-booking_date']

    def __str__(self) -> str:
        attendee_name = self.attendee.user.username if self.attendee and self.attendee.user else 'unknown'
        return f"Booking(attendee={attendee_name}, event={self.event_id}, status={self.status})"
