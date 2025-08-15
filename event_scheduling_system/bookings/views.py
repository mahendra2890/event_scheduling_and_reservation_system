from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Booking
from .serializers import BookingSerializer
from .permissions import IsBookingAttendeeOrEventOrganizer


class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBookingAttendeeOrEventOrganizer]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    queryset = Booking.objects.select_related('attendee__user', 'event').all()
    serializer_class = BookingSerializer
    """
    Minimal Booking CRUD:
    - GET /bookingapi/booking/ : list of all bookings for customers; booking for their own events for organizers
    - POST /bookingapi/booking/ : Creates a booking for customers, 403 for organisers
    - GET /bookingapi/booking/{id}/ : Attendee can see their bookings with ID; and organisers can see all bookings for their events with ID; 403 for other events' booking
    - PATCH /bookingapi/booking/{id}/ : Updates a booking, if booking's attendee; 403 for organisers
    - DELETE /bookingapi/booking/{id}/ : Hard deletes a booking, if booking's attendee; 403 for organisers
    """
    def get_queryset(self):
        if self.action == 'list':
            qs = self.queryset
            user = self.request.user
            has_c = hasattr(user, 'customer_profile')
            has_o = hasattr(user, 'organizer_profile')
            if has_c and has_o:
                return qs.filter(Q(attendee=user.customer_profile) | Q(event__creator=user.organizer_profile))
            if has_c:
                return qs.filter(attendee=user.customer_profile)
            if has_o:
                return qs.filter(event__creator=user.organizer_profile)
            return qs.none()
        return self.queryset