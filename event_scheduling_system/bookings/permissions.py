from rest_framework import permissions


class IsBookingAttendeeOrEventOrganizer(permissions.BasePermission):
    """
    Allow booking attendees full access to their bookings.
    Allow event organizers to read bookings for their own events.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Read-only allowed to any authenticated user (object-level will further restrict customers)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Create only for customers (attendees)
        if request.method == 'POST':
            return hasattr(request.user, 'customer_profile')

        # PATCH/DELETE/PUT only allowed to customers
        if request.method in ('PATCH', 'DELETE', 'PUT'):
            return hasattr(request.user, 'customer_profile')

        return False

    def has_object_permission(self, request, view, obj):
        # Booking attendee (customer) can do anything
        if hasattr(request.user, 'customer_profile') and obj.attendee_id == request.user.customer_profile.id:
            return True

        # Event organizer can read bookings for events they created
        if request.method in permissions.SAFE_METHODS and hasattr(request.user, 'organizer_profile'):
            return obj.event.creator_id == request.user.organizer_profile.id

        return False


