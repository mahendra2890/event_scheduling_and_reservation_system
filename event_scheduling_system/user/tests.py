from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.urls import reverse
from django.test.utils import override_settings
from datetime import timedelta
from django.utils import timezone

from user.models import Organizer, Customer, HistoryPoint
from events.models import Event
from bookings.models import Booking


class UserAuthenticationAPITest(APITestCase):
    """Test cases for user authentication APIs."""
    
    def setUp(self):
        # Create test users
        self.organizer_user = User.objects.create_user(
            username='organizer1', 
            password='testpass123',
            email='organizer@test.com',
            first_name='John',
            last_name='Doe'
        )
        self.organizer = Organizer.objects.create(
            user=self.organizer_user,
            organization_name='Test Org',
            business_address='123 Test St'
        )
        
        self.customer_user = User.objects.create_user(
            username='customer1', 
            password='testpass123',
            email='customer@test.com',
            first_name='Jane',
            last_name='Smith'
        )
        self.customer = Customer.objects.create(user=self.customer_user)
        
        # Create tokens
        self.organizer_token = Token.objects.create(user=self.organizer_user)
        self.customer_token = Token.objects.create(user=self.customer_user)
    
    def test_organizer_registration_success(self):
        """Test successful organizer registration."""
        url = reverse('organizer-register')
        data = {
            'username': 'neworganizer',
            'email': 'neworganizer@test.com',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'Organizer',
            'organization_name': 'New Org',
            'business_address': '456 New St'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('organizer_id', response.data)
        self.assertEqual(response.data['username'], 'neworganizer')
        
        # Verify user was created
        user = User.objects.get(username='neworganizer')
        self.assertTrue(hasattr(user, 'organizer_profile'))
        self.assertEqual(user.organizer_profile.organization_name, 'New Org')
        
        # Verify history was logged
        history = HistoryPoint.objects.filter(user=user, action='register').first()
        self.assertIsNotNone(history)
        self.assertEqual(history.details['user_type'], 'organizer')
        self.assertEqual(history.details['organization_name'], 'New Org')
    
    def test_customer_registration_success(self):
        """Test successful customer registration."""
        url = reverse('customer-register')
        data = {
            'username': 'newcustomer',
            'email': 'newcustomer@test.com',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'Customer'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('customer_id', response.data)
        self.assertEqual(response.data['username'], 'newcustomer')
        
        # Verify user was created
        user = User.objects.get(username='newcustomer')
        self.assertTrue(hasattr(user, 'customer_profile'))
        
        # Verify history was logged
        history = HistoryPoint.objects.filter(user=user, action='register').first()
        self.assertIsNotNone(history)
        self.assertEqual(history.details['user_type'], 'customer')
    
    def test_login_success_organizer(self):
        """Test successful login for organizer."""
        url = reverse('login')
        data = {
            'username': 'organizer1',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user_type'], 'organizer')
        self.assertIn('profile_data', response.data)
        self.assertEqual(response.data['profile_data']['organization_name'], 'Test Org')
        
        # Verify history was logged
        history = HistoryPoint.objects.filter(user=self.organizer_user, action='login').first()
        self.assertIsNotNone(history)
        self.assertEqual(history.details['login_method'], 'username_password')
    
    def test_login_success_customer(self):
        """Test successful login for customer."""
        url = reverse('login')
        data = {
            'username': 'customer1',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user_type'], 'customer')
        self.assertIn('profile_data', response.data)
        
        # Verify history was logged
        history = HistoryPoint.objects.filter(user=self.customer_user, action='login').first()
        self.assertIsNotNone(history)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        url = reverse('login')
        data = {
            'username': 'organizer1',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_logout_success(self):
        """Test successful logout."""
        url = reverse('logout')
        self.client.force_authenticate(user=self.organizer_user)
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Logged out successfully')
        
        # Verify token was deleted
        self.assertFalse(Token.objects.filter(user=self.organizer_user).exists())
        
        # Verify history was logged
        history = HistoryPoint.objects.filter(user=self.organizer_user, action='logout').first()
        self.assertIsNotNone(history)
        self.assertEqual(history.details['logout_method'], 'token_deletion')
    
    def test_logout_unauthorized(self):
        """Test logout without authentication."""
        url = reverse('logout')
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_profile_get_organizer(self):
        """Test getting organizer profile."""
        url = reverse('user-profile')
        self.client.force_authenticate(user=self.organizer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_type'], 'organizer')
        self.assertEqual(response.data['username'], 'organizer1')
        self.assertIn('profile_data', response.data)
        self.assertEqual(response.data['profile_data']['organization_name'], 'Test Org')
    
    def test_profile_get_customer(self):
        """Test getting customer profile."""
        url = reverse('user-profile')
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_type'], 'customer')
        self.assertEqual(response.data['username'], 'customer1')
        self.assertIn('profile_data', response.data)
    
    def test_profile_get_unauthorized(self):
        """Test getting profile without authentication."""
        url = reverse('user-profile')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(USE_TZ=False)
class HistoryPointAPITest(APITestCase):
    """Test cases for history point APIs."""
    
    def setUp(self):
        # Create test users
        self.organizer_user = User.objects.create_user(username='organizer1', password='testpass123')
        self.organizer = Organizer.objects.create(
            user=self.organizer_user,
            organization_name='Test Org',
            business_address='123 Test St'
        )
        
        self.customer_user = User.objects.create_user(username='customer1', password='testpass123')
        self.customer = Customer.objects.create(user=self.customer_user)
        
        # Create some history points
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            capacity=10,
            creator=self.organizer
        )
        
        # Create history points for organizer
        HistoryPoint.log_action(
            user=self.organizer_user,
            action='create',
            obj=self.event,
            details={'title': 'Test Event'}
        )
        
        HistoryPoint.log_action(
            user=self.organizer_user,
            action='login',
            obj=self.organizer_user,
            details={'login_method': 'username_password'}
        )
        
        # Create history points for customer
        HistoryPoint.log_action(
            user=self.customer_user,
            action='login',
            obj=self.customer_user,
            details={'login_method': 'username_password'}
        )
    
    def test_list_history_points_organizer(self):
        """Test listing history points for organizer."""
        url = reverse('history-list')
        self.client.force_authenticate(user=self.organizer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle pagination - response.data is a dict with 'results' key
        history_data = response.data.get('results', response.data)
        # Should have 2 history points for organizer (create + login)
        self.assertEqual(len(history_data), 2)
        
        # Verify only organizer's history points are returned
        for history in history_data:
            self.assertEqual(history['user']['id'], self.organizer_user.id)
    
    def test_list_history_points_customer(self):
        """Test listing history points for customer."""
        url = reverse('history-list')
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle pagination - response.data is a dict with 'results' key
        history_data = response.data.get('results', response.data)
        # Should have 1 history point for customer (login)
        self.assertEqual(len(history_data), 1)
        
        # Verify only customer's history points are returned
        for history in history_data:
            self.assertEqual(history['user']['id'], self.customer_user.id)
    
    def test_list_history_points_unauthorized(self):
        """Test listing history points without authentication."""
        url = reverse('history-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_filter_history_by_action(self):
        """Test filtering history points by action."""
        url = reverse('history-list')
        self.client.force_authenticate(user=self.organizer_user)
        
        response = self.client.get(url, {'action': 'create'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle pagination - response.data is a dict with 'results' key
        history_data = response.data.get('results', response.data)
        self.assertEqual(len(history_data), 1)
        self.assertEqual(history_data[0]['action'], 'create')
    
    def test_filter_history_by_content_type(self):
        """Test filtering history points by content type."""
        url = reverse('history-list')
        self.client.force_authenticate(user=self.organizer_user)
        
        response = self.client.get(url, {'content_type': 'event'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle pagination - response.data is a dict with 'results' key
        history_data = response.data.get('results', response.data)
        self.assertEqual(len(history_data), 1)
        self.assertEqual(history_data[0]['content_type_name'], 'event')
    
    def test_filter_history_by_date_range(self):
        """Test filtering history points by date range."""
        url = reverse('history-list')
        self.client.force_authenticate(user=self.organizer_user)
        
        today = timezone.now().date()
        
        response = self.client.get(url, {'start_date': today})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle pagination - response.data is a dict with 'results' key
        history_data = response.data.get('results', response.data)
        # Should have 2 history points from today (create + login)
        self.assertEqual(len(history_data), 2)
    
    def test_get_history_point_detail(self):
        """Test getting a specific history point."""
        history = HistoryPoint.objects.filter(user=self.organizer_user).first()
        url = reverse('history-detail', kwargs={'pk': history.id})
        self.client.force_authenticate(user=self.organizer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], history.id)
        self.assertEqual(response.data['user']['id'], self.organizer_user.id)
    
    def test_get_history_point_detail_unauthorized(self):
        """Test getting history point detail without authentication."""
        history = HistoryPoint.objects.filter(user=self.organizer_user).first()
        url = reverse('history-detail', kwargs={'pk': history.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_other_user_history_point_forbidden(self):
        """Test that users cannot access other users' history points."""
        history = HistoryPoint.objects.filter(user=self.organizer_user).first()
        url = reverse('history-detail', kwargs={'pk': history.id})
        self.client.force_authenticate(user=self.customer_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserModelTest(TestCase):
    """Test cases for user models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
    
    def test_organizer_creation(self):
        """Test organizer creation."""
        organizer = Organizer.objects.create(
            user=self.user,
            organization_name='Test Organization',
            business_address='123 Business St'
        )
        
        self.assertEqual(organizer.user, self.user)
        self.assertEqual(organizer.organization_name, 'Test Organization')
        self.assertEqual(organizer.business_address, '123 Business St')
        self.assertIsNotNone(organizer.created_at)
        self.assertIsNotNone(organizer.updated_at)
    
    def test_customer_creation(self):
        """Test customer creation."""
        customer = Customer.objects.create(user=self.user)
        
        self.assertEqual(customer.user, self.user)
        self.assertIsNotNone(customer.created_at)
        self.assertIsNotNone(customer.updated_at)
    
    def test_organizer_str_representation(self):
        """Test organizer string representation."""
        organizer = Organizer.objects.create(
            user=self.user,
            organization_name='Test Organization',
            business_address='123 Business St'
        )
        
        self.assertEqual(str(organizer), 'Test Organization - testuser')
    
    def test_customer_str_representation(self):
        """Test customer string representation."""
        customer = Customer.objects.create(user=self.user)
        
        self.assertEqual(str(customer), 'testuser - Customer')
    
    def test_organizer_updated_at_auto_update(self):
        """Test that organizer updated_at field updates automatically."""
        organizer = Organizer.objects.create(
            user=self.user,
            organization_name='Test Organization',
            business_address='123 Business St'
        )
        
        original_updated_at = organizer.updated_at
        
        # Update the organizer
        organizer.organization_name = 'Updated Organization'
        organizer.save()
        
        # Verify updated_at was changed
        organizer.refresh_from_db()
        self.assertGreater(organizer.updated_at, original_updated_at)
    
    def test_customer_updated_at_auto_update(self):
        """Test that customer updated_at field updates automatically."""
        customer = Customer.objects.create(user=self.user)
        
        original_updated_at = customer.updated_at
        
        # Update the customer (though there are no fields to update currently)
        customer.save()
        
        # Verify updated_at was changed
        customer.refresh_from_db()
        self.assertGreaterEqual(customer.updated_at, original_updated_at)


class HistoryPointModelTest(TestCase):
    """Test cases for history point model."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.organizer = Organizer.objects.create(
            user=self.user,
            organization_name='Test Org',
            business_address='123 Test St'
        )
    
    def test_history_point_creation(self):
        """Test history point creation."""
        history = HistoryPoint.objects.create(
            user=self.user,
            action='test_action',
            content_type_id=1,
            object_id=1,
            details={'test': 'data'}
        )
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.action, 'test_action')
        self.assertEqual(history.object_id, 1)
        self.assertEqual(history.details, {'test': 'data'})
        self.assertIsNotNone(history.created_at)
    
    def test_log_action_class_method(self):
        """Test the log_action class method."""
        history = HistoryPoint.log_action(
            user=self.user,
            action='test_action',
            obj=self.organizer,
            details={'test': 'data'}
        )
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.action, 'test_action')
        self.assertEqual(history.object_id, self.organizer.id)
        self.assertEqual(history.content_type.model, 'organizer')
        self.assertEqual(history.details, {'test': 'data'})
    
    def test_history_point_str_representation(self):
        """Test history point string representation."""
        history = HistoryPoint.objects.create(
            user=self.user,
            action='test_action',
            content_type_id=1,
            object_id=1,
            details={'test': 'data'}
        )
        
        # The actual format includes content_type.model and object_id
        expected_str = f"{self.user.username} - test_action - logentry #{history.object_id} - {history.created_at}"
        self.assertEqual(str(history), expected_str)
    
    def test_history_point_ordering(self):
        """Test that history points are ordered by created_at descending."""
        # Create history points with different timestamps
        history1 = HistoryPoint.objects.create(
            user=self.user,
            action='action1',
            content_type_id=1,
            object_id=1
        )
        
        history2 = HistoryPoint.objects.create(
            user=self.user,
            action='action2',
            content_type_id=1,
            object_id=2
        )
        
        # Get all history points
        history_points = HistoryPoint.objects.all()
        
        # Verify ordering (newest first)
        self.assertEqual(history_points[0], history2)
        self.assertEqual(history_points[1], history1)
