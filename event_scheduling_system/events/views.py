from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Event
from .serializers import EventSerializer
from .permissions import IsEventCreatorOrCustomerReadOnly
from user.models import HistoryPoint


class EventViewSet(viewsets.ModelViewSet):
    """
    Minimal Event CRUD:
    - GET /eventapi/event/ : list of all events for organisers and customers
    - POST /eventapi/event/ : Creates an event for organisers, 403 for customers
    - GET /eventapi/event/{id}/ : Creator can see their events with ID; and customers can see all events with ID
    - PATCH /eventapi/event/{id}/ : Updates an event, if event's creator; 403 for customers
    - DELETE /eventapi/event/{id}/ : Hard deletes an event, if event's creator; 403 for customers
    - GET /eventapi/event/my_events/ : Lists creator's events; 403 for customers
    - GET /eventapi/event/upcoming/ : Lists upcoming events for organisers and customers
    - GET /eventapi/event/past/ : list past events for organisers and customers
    """
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsEventCreatorOrCustomerReadOnly]

    def create(self, request, *args, **kwargs):
        """
        Create an event and log the action.
        """
        # Get the serializer and validate data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        
        HistoryPoint.log_action(
            user=request.user,
            action=HistoryPoint.ACTION_CREATE,
            obj=event,
            details={
                'title': event.title,
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat(),
                'capacity': event.capacity,
                'creator_id': event.creator.id
            }
        )
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Update an event and log the action.
        """
        # Get the instance before update to capture original values
        instance = self.get_object()
        old_values = {
            'title': instance.title,
            'description': instance.description,
            'start_time': instance.start_time.isoformat(),
            'end_time': instance.end_time.isoformat(),
            'capacity': instance.capacity
        }
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            # Get the updated instance from the response
            updated_instance = self.get_object()
            HistoryPoint.log_action(
                user=request.user,
                action=HistoryPoint.ACTION_UPDATE,
                obj=updated_instance,
                details={
                    'old_values': old_values,
                    'new_values': {
                        'title': updated_instance.title,
                        'description': updated_instance.description,
                        'start_time': updated_instance.start_time.isoformat(),
                        'end_time': updated_instance.end_time.isoformat(),
                        'capacity': updated_instance.capacity
                    },
                    'updated_fields': list(request.data.keys()) if request.data else []
                }
            )
        
        return response

    def _get_paginated_response(self, queryset):
        """
        Helper method to handle pagination for custom actions.
        """
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """
        List events created by the authenticated organizer.
        """
        if not hasattr(request.user, 'organizer_profile'):
            return Response(
                {'detail': 'Only organizers have events.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = Event.objects.filter(creator=request.user.organizer_profile)
        return self._get_paginated_response(queryset)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        List upcoming events (events that haven't started yet).
        """
        queryset = Event.objects.filter(start_time__gt=timezone.now())
        return self._get_paginated_response(queryset)

    @action(detail=False, methods=['get'])
    def past(self, request):
        """
        List past events (events that have already ended).
        """
        queryset = Event.objects.filter(end_time__lt=timezone.now())
        return self._get_paginated_response(queryset)
