from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Event
from .serializers import EventSerializer
from .permissions import IsEventCreatorOrCustomerReadOnly


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

    @action(detail=False, methods=['get'])
    def my_events(self, request):
        if not hasattr(request.user, 'organizer_profile'):
            return Response({'detail': 'Only organizers have events.'}, status=status.HTTP_403_FORBIDDEN)
        qs = Event.objects.filter(creator=request.user.organizer_profile)
        page = self.paginate_queryset(qs)
        if page is not None:
            s = self.get_serializer(page, many=True)
            return self.get_paginated_response(s.data)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        qs = Event.objects.filter(start_time__gt=timezone.now())
        page = self.paginate_queryset(qs)
        if page is not None:
            s = self.get_serializer(page, many=True)
            return self.get_paginated_response(s.data)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def past(self, request):
        qs = Event.objects.filter(end_time__lt=timezone.now())
        page = self.paginate_queryset(qs)
        if page is not None:
            s = self.get_serializer(page, many=True)
            return self.get_paginated_response(s.data)
        return Response(self.get_serializer(qs, many=True).data)
