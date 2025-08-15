from rest_framework import serializers
from .models import Event
from user.serializers import OrganizerSerializer


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model."""
    
    creator = OrganizerSerializer(read_only=True)
    available_slots = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'start_time', 'end_time',
            'capacity', 'available_slots', 'is_full', 'creator', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Custom validation for event data.
        """
        # Check if end_time is after start_time
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })
        
        # Check if capacity is at least 1
        capacity = data.get('capacity')
        if capacity and capacity < 1:
            raise serializers.ValidationError({
                'capacity': 'Capacity must be at least 1.'
            })
        
        return data

    def create(self, validated_data):
        """
        Create a new event and set the creator to the authenticated user.
        """
        validated_data['creator'] = self.context['request'].user.organizer_profile
        return super().create(validated_data)