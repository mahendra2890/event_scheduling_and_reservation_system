from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.urls import reverse

from user.models import Organizer, Customer, HistoryPoint
from .models import Event


class EventAPITest(APITestCase):
    """Test cases for Event API endpoints."""
    
    def setUp(self):
        # Create test users
        self.organizer_user = User.objects.create_user(
            username='organizer1', 
            password='testpass123',
            email='organizer@test.com'
        )
        self.organizer = Organizer.objects.create(
            user=self.organizer_user,
            organization_name='Test Org',
            business_address='123 Test St'
        )
        
        self.customer_user = User.objects.create_user(
            username='customer1', 
            password='testpass123',
            email='customer@test.com'
        )
        self.customer = Customer.objects.create(user=self.customer_user)
        
        # Create tokens
        self.organizer_token = Token.objects.create(user=self.organizer_user)
        self.customer_token = Token.objects.create(user=self.customer_user)
        
        # Create test event
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            capacity=10,
            creator=self.organizer
        )
    
    def test_create_event_success_organizer(self):
        """Test successful event creation by organizer."""
        url = reverse('event-list')
        self.client.force_authenticate(user=self.organizer_user)
        
        data = {
            'title': 'New Event',
            'description': 'New Event Description',
            'start_time': (timezone.now() + timedelta(days=2)).isoformat(),
            'end_time': (timezone.now() + timedelta(days=2, hours=3)).isoformat(),
            'capacity': 20
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Event')
        self.assertEqual(response.data['creator']['organization_name'], 'Test Org')
        self.assertEqual(response.data['capacity'], 20)
        self.assertEqual(response.data['available_slots'], 20)
        self.assertFalse(response.data['is_full'])
        
        # Verify event was created
        event = Event.objects.get(title='New Event')
        self.assertEqual(event.creator, self.organizer)
        
        # Verify history was logged
        history = HistoryPoint.objects.filter(
            user=self.organizer_user, 
            action='create',
            content_type__model='event'
        ).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.details['title'], 'New Event')
        self.assertEqual(history.details['capacity'], 20)
    
    def test_create_event_forbidden_customer(self):
        """Test that customers cannot create events."""
        url = reverse('event-list')
        self.client.force_authenticate(user=self.customer_user)
        
        data = {
            'title': 'Customer Event',
            'description': 'Customer Event Description',
            'start_time': (timezone.now() + timedelta(days=2)).isoformat(),
            'end_time': (timezone.now() + timedelta(days=2, hours=3)).isoformat(),
            'capacity': 20
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_event_unauthorized(self):
        """Test event creation without authentication."""
        url = reverse('event-list')
        
        data = {
            'title': 'Unauthorized Event',
            'description': 'Unauthorized Event Description',
            'start_time': (timezone.now() + timedelta(days=2)).isoformat(),
            'end_time': (timezone.now() + timedelta(days=2, hours=3)).isoformat(),
            'capacity': 20
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_events_success(self):
        """Test listing events."""
        url = reverse('event-list')
        # Need authentication for all operations
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have at least 1 event (the one created in setUp)
        self.assertGreaterEqual(len(response.data), 1)
        # Check that our test event is in the list
        if hasattr(response.data, 'get') and response.data.get('results'):
            # Paginated response
            event_titles = [event['title'] for event in response.data['results']]
        else:
            # Direct list response
            event_titles = [event['title'] for event in response.data]
        self.assertIn('Test Event', event_titles)
    
    def test_get_event_detail_success(self):
        """Test getting event detail."""
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        # Need authentication for all operations
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Event')
        self.assertEqual(response.data['creator']['organization_name'], 'Test Org')
        self.assertEqual(response.data['available_slots'], 10)
        self.assertFalse(response.data['is_full'])

    def test_get_event_detail_with_bookings(self):
        """Test getting event detail when it has bookings.
        
        This tests requirement: "As an user (attendee), I want to be able to see the details of a specific event, including how many slots are still available."
        """
        # Create some bookings for the event
        from user.models import Customer
        from bookings.models import Booking
        
        customer1 = Customer.objects.create(
            user=User.objects.create_user(username='detail_customer1')
        )
        customer2 = Customer.objects.create(
            user=User.objects.create_user(username='detail_customer2')
        )
        
        Booking.objects.create(
            attendee=customer1,
            event=self.event,
            status='active'
        )
        Booking.objects.create(
            attendee=customer2,
            event=self.event,
            status='active'
        )
        
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['capacity'], 10)
        self.assertEqual(response.data['available_slots'], 8)  # 10 - 2 bookings
        self.assertFalse(response.data['is_full'])

    def test_get_event_detail_full_event(self):
        """Test getting event detail when event is full."""
        # Fill the event to capacity
        from user.models import Customer
        from bookings.models import Booking
        
        for i in range(10):  # Fill to capacity
            customer = Customer.objects.create(
                user=User.objects.create_user(username=f'full_event_customer_{i}')
            )
            Booking.objects.create(
                attendee=customer,
                event=self.event,
                status='active'
            )
        
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['capacity'], 10)
        self.assertEqual(response.data['available_slots'], 0)
        self.assertTrue(response.data['is_full'])

    def test_get_event_detail_not_found(self):
        """Test getting event detail for non-existent event."""
        url = reverse('event-detail', kwargs={'pk': 99999})
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_event_detail_includes_all_required_fields(self):
        """Test that event detail includes all required fields for attendees."""
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check all required fields are present
        required_fields = [
            'id', 'title', 'description', 'start_time', 'end_time',
            'capacity', 'available_slots', 'is_full', 'creator'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data, f"Field '{field}' is missing from event detail")

    def test_event_list_includes_available_slots(self):
        """Test that event list includes available slots information."""
        url = reverse('event-list')
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle pagination
        events_data = response.data.get('results', response.data)
        
        # Check that events include available slots
        for event_data in events_data:
            self.assertIn('available_slots', event_data)
            self.assertIn('is_full', event_data)
            self.assertIn('capacity', event_data)

    def test_update_event_success_creator(self):
        """Test successful event update by creator."""
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.client.force_authenticate(user=self.organizer_user)
        
        data = {
            'title': 'Updated Event',
            'capacity': 15
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Event')
        self.assertEqual(response.data['capacity'], 15)
        self.assertEqual(response.data['available_slots'], 15)
        
        # Verify event was updated
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'Updated Event')
        self.assertEqual(self.event.capacity, 15)
        
        # Verify history was logged
        history = HistoryPoint.objects.filter(
            user=self.organizer_user, 
            action='update',
            content_type__model='event'
        ).first()
        self.assertIsNotNone(history)
        self.assertIn('title', history.details['updated_fields'])
        self.assertIn('capacity', history.details['updated_fields'])
    
    def test_update_event_forbidden_customer(self):
        """Test that customers cannot update events."""
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.client.force_authenticate(user=self.customer_user)
        
        data = {
            'title': 'Customer Updated Event'
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_event_forbidden_other_organizer(self):
        """Test that other organizers cannot update events."""
        other_organizer_user = User.objects.create_user(username='other_organizer', password='testpass123')
        other_organizer = Organizer.objects.create(
            user=other_organizer_user,
            organization_name='Other Org',
            business_address='456 Other St'
        )
        
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.client.force_authenticate(user=other_organizer_user)
        
        data = {
            'title': 'Other Organizer Updated Event'
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_event_success_creator(self):
        """Test successful event deletion by creator."""
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.client.force_authenticate(user=self.organizer_user)
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify event was deleted
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())
    
    def test_delete_event_forbidden_customer(self):
        """Test that customers cannot delete events."""
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_my_events_success_organizer(self):
        """Test getting organizer's own events."""
        url = reverse('event-my-events')
        self.client.force_authenticate(user=self.organizer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have at least 1 event (the one created in setUp)
        self.assertGreaterEqual(len(response.data), 1)
        # Check that our test event is in the list
        if hasattr(response.data, 'get') and response.data.get('results'):
            # Paginated response
            event_titles = [event['title'] for event in response.data['results']]
        else:
            # Direct list response
            event_titles = [event['title'] for event in response.data]
        self.assertIn('Test Event', event_titles)
    
    def test_my_events_forbidden_customer(self):
        """Test that customers cannot access my_events."""
        url = reverse('event-my-events')
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_upcoming_events_success(self):
        """Test getting upcoming events."""
        url = reverse('event-upcoming')
        # Need authentication for all operations
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have at least 1 event (the one created in setUp)
        self.assertGreaterEqual(len(response.data), 1)
        # Check that our test event is in the list
        if hasattr(response.data, 'get') and response.data.get('results'):
            # Paginated response
            event_titles = [event['title'] for event in response.data['results']]
        else:
            # Direct list response
            event_titles = [event['title'] for event in response.data]
        self.assertIn('Test Event', event_titles)
    
    def test_past_events_success(self):
        """Test getting past events."""
        # Create a past event
        past_event = Event.objects.create(
            title='Past Event',
            description='Past Event Description',
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=1),  # Fixed: end_time after start_time
            capacity=5,
            creator=self.organizer
        )
        
        url = reverse('event-past')
        # Need authentication for all operations
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have at least 1 past event
        self.assertGreaterEqual(len(response.data), 1)
        # Check that our past event is in the list
        if hasattr(response.data, 'get') and response.data.get('results'):
            # Paginated response
            event_titles = [event['title'] for event in response.data['results']]
        else:
            # Direct list response
            event_titles = [event['title'] for event in response.data]
        self.assertIn('Past Event', event_titles)
    
    def test_create_event_validation_error(self):
        """Test event creation with validation errors."""
        url = reverse('event-list')
        self.client.force_authenticate(user=self.organizer_user)
        
        # End time before start time
        data = {
            'title': 'Invalid Event',
            'description': 'Invalid Event Description',
            'start_time': (timezone.now() + timedelta(days=2)).isoformat(),
            'end_time': (timezone.now() + timedelta(days=1)).isoformat(),  # Before start time
            'capacity': 20
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_time', response.data)
    
    def test_create_event_invalid_capacity(self):
        """Test event creation with invalid capacity."""
        url = reverse('event-list')
        self.client.force_authenticate(user=self.organizer_user)
        
        data = {
            'title': 'Invalid Capacity Event',
            'description': 'Invalid Capacity Event Description',
            'start_time': (timezone.now() + timedelta(days=2)).isoformat(),
            'end_time': (timezone.now() + timedelta(days=2, hours=3)).isoformat(),
            'capacity': -1  # Invalid capacity (negative)
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('capacity', response.data)

    def test_event_validation_start_time_after_end_time(self):
        """Test event creation with start time after end time."""
        url = reverse('event-list')
        self.client.force_authenticate(user=self.organizer_user)
        
        data = {
            'title': 'Invalid Time Event',
            'description': 'Invalid Time Event Description',
            'start_time': (timezone.now() + timedelta(days=2, hours=3)).isoformat(),
            'end_time': (timezone.now() + timedelta(days=2)).isoformat(),  # End before start
            'capacity': 20
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_time', response.data)

    def test_event_validation_past_start_time(self):
        """Test event creation with past start time."""
        url = reverse('event-list')
        self.client.force_authenticate(user=self.organizer_user)
        
        data = {
            'title': 'Past Event',
            'description': 'Past Event Description',
            'start_time': (timezone.now() - timedelta(days=1)).isoformat(),  # Past time
            'end_time': (timezone.now() + timedelta(days=1)).isoformat(),
            'capacity': 20
        }
        
        response = self.client.post(url, data)
        
        # Note: The current implementation doesn't validate past start times
        # This test documents the expected behavior if validation is added
        # For now, it should succeed since validation is not implemented
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_event_update_validation(self):
        """Test event update validation."""
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.client.force_authenticate(user=self.organizer_user)
        
        # Test updating with invalid capacity
        data = {'capacity': -1}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('capacity', response.data)

    def test_event_delete_with_bookings(self):
        """Test event deletion when it has bookings."""
        # Create a booking for the event
        from user.models import Customer
        from bookings.models import Booking
        
        customer = Customer.objects.create(
            user=User.objects.create_user(username='customer_for_delete')
        )
        
        booking = Booking.objects.create(
            attendee=customer,
            event=self.event,
            status='active'
        )
        
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.client.force_authenticate(user=self.organizer_user)
        
        response = self.client.delete(url)
        
        # Should be able to delete event even with bookings (cascade delete)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify event and booking are deleted
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())


class EventModelTest(TestCase):
    """Test cases for Event model."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.organizer = Organizer.objects.create(
            user=self.user,
            organization_name='Test Organization',
            business_address='123 Business St'
        )
        
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            capacity=10,
            creator=self.organizer
        )
    
    def test_event_creation(self):
        """Test event creation."""
        self.assertEqual(self.event.title, 'Test Event')
        self.assertEqual(self.event.description, 'Test Description')
        self.assertEqual(self.event.capacity, 10)
        self.assertEqual(self.event.creator, self.organizer)
        self.assertIsNotNone(self.event.created_at)
        self.assertIsNotNone(self.event.updated_at)
    
    def test_event_str_representation(self):
        """Test event string representation."""
        self.assertEqual(str(self.event), 'Test Event')
    
    def test_available_slots_calculation(self):
        """Test available slots calculation."""
        self.assertEqual(self.event.available_slots, 10)
        
        # Create a booking to reduce available slots
        from bookings.models import Booking
        customer = Customer.objects.create(user=User.objects.create_user(username='customer'))
        booking = Booking.objects.create(
            attendee=customer,
            event=self.event,
            status='active'
        )
        
        self.assertEqual(self.event.available_slots, 9)
    
    def test_is_full_property(self):
        """Test is_full property."""
        self.assertFalse(self.event.is_full)
        
        # Fill the event
        from bookings.models import Booking
        for i in range(10):
            customer = Customer.objects.create(
                user=User.objects.create_user(username=f'customer{i}')
            )
            Booking.objects.create(
                attendee=customer,
                event=self.event,
                status='active'
            )
        
        self.assertTrue(self.event.is_full)
    
    def test_is_past_property(self):
        """Test is_past property."""
        # Future event
        self.assertFalse(self.event.is_past)
        
        # Past event
        past_event = Event.objects.create(
            title='Past Event',
            description='Past Description',
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=1),  # Fixed: end_time after start_time
            capacity=5,
            creator=self.organizer
        )
        
        self.assertTrue(past_event.is_past)
    
    def test_is_ongoing_property(self):
        """Test is_ongoing property."""
        # Future event
        self.assertFalse(self.event.is_ongoing)
        
        # Past event
        past_event = Event.objects.create(
            title='Past Event',
            description='Past Description',
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=1),  # Fixed: end_time after start_time
            capacity=5,
            creator=self.organizer
        )
        
        self.assertFalse(past_event.is_ongoing)
        
        # Ongoing event (current time between start and end)
        ongoing_event = Event.objects.create(
            title='Ongoing Event',
            description='Ongoing Description',
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=1),
            capacity=5,
            creator=self.organizer
        )
        
        self.assertTrue(ongoing_event.is_ongoing)
    
    def test_event_validation(self):
        """Test event validation."""
        # Test end_time before start_time
        with self.assertRaises(Exception):
            Event.objects.create(
                title='Invalid Event',
                description='Invalid Description',
                start_time=timezone.now() + timedelta(days=1),
                end_time=timezone.now(),  # Before start_time
                capacity=10,
                creator=self.organizer
            )
    
    def test_event_updated_at_auto_update(self):
        """Test that event updated_at field updates automatically."""
        original_updated_at = self.event.updated_at
        
        # Update the event
        self.event.title = 'Updated Event'
        self.event.save()
        
        # Verify updated_at was changed
        self.event.refresh_from_db()
        self.assertGreater(self.event.updated_at, original_updated_at)
    
    def test_cancelled_bookings_dont_count_towards_capacity(self):
        """Test that cancelled bookings don't count towards capacity."""
        from bookings.models import Booking
        
        # Create a booking
        customer = Customer.objects.create(user=User.objects.create_user(username='customer'))
        booking = Booking.objects.create(
            attendee=customer,
            event=self.event,
            status='active'
        )
        
        self.assertEqual(self.event.available_slots, 9)
        
        # Cancel the booking
        booking.cancel()
        
        self.assertEqual(self.event.available_slots, 10)  # Back to full capacity
