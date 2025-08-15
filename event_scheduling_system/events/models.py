from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from user.models import Organizer


class Event(models.Model):
    """
    Event model for managing events in the scheduling system.
    """
    title = models.CharField(max_length=200, help_text="Event title")
    description = models.TextField(blank=True, null=True, help_text="Event description")
    start_time = models.DateTimeField(help_text="Event start time")
    end_time = models.DateTimeField(help_text="Event end time")
    capacity = models.PositiveIntegerField(help_text="Maximum number of attendees")
    creator = models.ForeignKey(
        Organizer, 
        on_delete=models.CASCADE, 
        related_name='created_events',
        help_text="Event creator"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return self.title

    def clean(self):
        """Custom validation for the model."""
        super().clean()
        
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError({
                    'end_time': 'End time must be after start time.'
                })
        
        # Check if capacity is at least 1
        if self.capacity and self.capacity < 1:
            raise ValidationError({
                'capacity': 'Capacity must be at least 1.'
            })

    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def available_slots(self):
        """
        Calculate available slots based on active bookings.
        """
        active_bookings_count = self.bookings.filter(status='active').count()
        return max(0, self.capacity - active_bookings_count)

    @property
    def is_full(self):
        """Check if the event is at full capacity."""
        return self.available_slots <= 0

    @property
    def is_past(self):
        """Check if the event has already ended."""
        return timezone.now() > self.end_time

    @property
    def is_ongoing(self):
        """Check if the event is currently ongoing."""
        now = timezone.now()
        return self.start_time <= now <= self.end_time
