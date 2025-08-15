from rest_framework import permissions


class IsEventCreatorOrCustomerReadOnly(permissions.BasePermission):
	"""
	Customers: read-only for all events.
	Organizers: POST; and GET/PATCH/DELETE only own events.
	"""

	def has_permission(self, request, view):
		# Must be authenticated
		if not request.user or not request.user.is_authenticated:
			return False

		# Read-only allowed to any authenticated user (object-level will further restrict organizers)
		if request.method in permissions.SAFE_METHODS:
			return True

		# Create only for organizers
		if request.method == 'POST':
			return hasattr(request.user, 'organizer_profile')

		# For PATCH/DELETE, defer to object-level check
		return True

	def has_object_permission(self, request, view, obj):
		# Read: customers can read all; organizers only their own
		if request.method in permissions.SAFE_METHODS:
			if hasattr(request.user, 'organizer_profile'):
				return obj.creator == request.user.organizer_profile
			return True  # customers (and non-organizer users) can read all

		# Write: only organizer-creator
		return hasattr(request.user, 'organizer_profile') and obj.creator == request.user.organizer_profile
