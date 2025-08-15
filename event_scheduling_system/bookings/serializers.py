from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .models import Booking
from user.models import Customer, HistoryPoint


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'attendee', 'event', 'booking_date', 'status']
        read_only_fields = ['id', 'attendee', 'booking_date']

    def validate(self, attrs):
        """
        Comprehensive validation for booking creation and updates.
        """
        event = attrs.get('event', getattr(self.instance, 'event', None))
        user = self.context['request'].user
        # Ensure user is a customer (for both create and update operations)
        if not hasattr(user, 'customer_profile'):
            raise serializers.ValidationError({
                'attendee': 'Only customers can create or update bookings.'
            })
        
        if not event:
            raise serializers.ValidationError({'event': 'Event is required.'})
        if event.is_past:
            raise serializers.ValidationError({
                'event': 'Cannot book for events that have already ended.'
            })
        if event.is_ongoing:
            raise serializers.ValidationError({
                'event': 'Cannot book for events that are currently ongoing.'
            })
        # Check if user already has an active booking for this event
        existing_booking = Booking.objects.filter(
            attendee__user=user,
            event=event,
            status='active'
        )
        
        # For updates, exclude the current booking from the check
        if self.instance:
            existing_booking = existing_booking.exclude(id=self.instance.id)
        
        if existing_booking.exists():
            raise serializers.ValidationError({
                'event': 'You already have an active booking for this event.'
            })
        
        # Capacity validation for create operations and reactivation
        if event.is_full and (not self.instance or 
                             (self.instance and self.instance.status == 'cancelled' and 
                              attrs.get('status') == 'active')):
            raise serializers.ValidationError({
                'event': 'This event is at full capacity. No more bookings available.'
            })
        
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        Create booking with atomic transaction to prevent race conditions.
        """
        user = self.context['request'].user
        
        validated_data['attendee'] = user.customer_profile
        event = validated_data['event']
        
        # Refresh event from database to get latest booking count
        event.refresh_from_db()
        
        booking = super().create(validated_data)
        return booking