from rest_framework import serializers
from .models import Booking
from user.models import Customer


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'attendee', 'event', 'booking_date', 'status']
        read_only_fields = ['id', 'booking_date']

    def create(self, validated_data):
        # map authenticated user to their customer profile
        user = self.context['request'].user
        if not hasattr(user, 'customer_profile'):
            raise serializers.ValidationError({'attendee': 'Only customers can create bookings.'})
        validated_data['attendee'] = user.customer_profile
        return super().create(validated_data)

    def validate(self, attrs):
        # basic presence/consistency checks can go here if needed
        return attrs


