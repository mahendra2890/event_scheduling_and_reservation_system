from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q

from .models import Booking
from .serializers import BookingSerializer
from .permissions import IsBookingAttendeeOrEventOrganizer
from user.models import HistoryPoint


class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsBookingAttendeeOrEventOrganizer]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    queryset = Booking.objects.select_related('attendee__user', 'event').all()
    serializer_class = BookingSerializer
    """
    Booking CRUD:
    - GET /bookingapi/booking/ : list of all bookings for customers; booking for their own events for organizers
    - POST /bookingapi/booking/ : Creates a booking for customers, 403 for organisers
    - GET /bookingapi/booking/{id}/ : Attendee can see their bookings with ID; and organisers can see all bookings for their events with ID; 403 for other events' booking
    - PATCH /bookingapi/booking/{id}/ : Updates a booking, if booking's attendee; 403 for organisers
    - DELETE /bookingapi/booking/{id}/ : Hard deletes a booking, if booking's attendee; 403 for organisers
    - POST /bookingapi/booking/{id}/cancel/ : Cancels a booking, if booking's attendee; 403 for organisers
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

    def create(self, request, *args, **kwargs):
        """
        Create a booking and log the action.
        """
        # Get the serializer and validate data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        HistoryPoint.log_action(
            user=request.user,
            action=HistoryPoint.ACTION_CREATE,
            obj=booking,
            details={
                'event_id': booking.event.id,
                'event_title': booking.event.title,
                'booking_date': booking.booking_date.isoformat(),
                'status': booking.status
            }
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Update a booking and log the action.
        """
        instance = self.get_object()
        original_status = instance.status
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == 200:
            updated_instance = self.get_object()
            action = HistoryPoint.ACTION_REACTIVATE if (
                original_status == 'cancelled' and updated_instance.status == 'active'
            ) else HistoryPoint.ACTION_UPDATE
            
            HistoryPoint.log_action(
                user=request.user,
                action=action,
                obj=updated_instance,
                details={
                    'previous_status': original_status,
                    'new_status': updated_instance.status,
                    'event_id': updated_instance.event.id,
                    'event_title': updated_instance.event.title,
                    'updated_fields': list(request.data.keys()) if request.data else []
                }
            )
        
        return response

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a booking.
        Only the booking attendee can cancel their own booking.
        """
        booking = self.get_object()
        
        try:
            booking.cancel()
            HistoryPoint.log_action(
                user=request.user,
                action='cancel',
                obj=booking,
                details={
                    'previous_status': 'active',
                    'new_status': 'cancelled',
                    'event_id': booking.event.id,
                    'event_title': booking.event.title
                }
            )
            
            return Response({
                'message': 'Booking cancelled successfully.',
                'booking_id': booking.id,
                'status': booking.status
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)