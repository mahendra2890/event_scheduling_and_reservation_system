from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, OpenApiExample

from user.serializers import (
    OrganizerSerializer, CustomerSerializer,
    OrganizerRegistrationSerializer, CustomerRegistrationSerializer,
    LoginSerializer
)
from user.models import Organizer, Customer


class OrganizerRegistrationView(APIView):
    """
    API endpoint for Organizer registration. Only allow POST requests.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=OrganizerRegistrationSerializer,
        responses={201: OrganizerRegistrationSerializer},
        examples=[
            OpenApiExample(
                'Organizer Registration Example',
                value={
                    'username': 'organizer1',
                    'email': 'organizer@example.com',
                    'password': 'securepassword123',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'organization_name': 'Event Pro',
                    'business_address': '123 Main St, City, State'
                }
            )
        ]
    )
    def post(self, request):
        serializer = OrganizerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            organizer = serializer.save()
            # Create token for the new user
            token, created = Token.objects.get_or_create(user=organizer.user)
            return Response({
                'message': 'Organizer registered successfully',
                'organizer_id': organizer.id,
                'username': organizer.user.username,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerRegistrationView(APIView):
    """
    API endpoint for Customer registration. Only allow POST requests.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=CustomerRegistrationSerializer,
        responses={201: CustomerRegistrationSerializer},
        examples=[
            OpenApiExample(
                'Customer Registration Example',
                value={
                    'username': 'customer1',
                    'email': 'customer@example.com',
                    'password': 'securepassword123',
                    'first_name': 'Jane',
                    'last_name': 'Smith'
                }
            )
        ]
    )
    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            # Create token for the new user
            token, created = Token.objects.get_or_create(user=customer.user)
            return Response({
                'message': 'Customer registered successfully',
                'customer_id': customer.id,
                'username': customer.user.username,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    API endpoint for user login. Only allow POST requests.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: LoginSerializer},
        examples=[
            OpenApiExample(
                'Login Example',
                value={
                    'username': 'user1',
                    'password': 'password123'
                }
            )
        ]
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            
            # Determine user type and return appropriate data
            response_data = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'token': token.key
            }
            
            # Check if user is an organizer
            if hasattr(user, 'organizer_profile'):
                response_data['user_type'] = 'organizer'
                response_data['profile_data'] = OrganizerSerializer(user.organizer_profile).data
            # Check if user is a customer
            elif hasattr(user, 'customer_profile'):
                response_data['user_type'] = 'customer'
                response_data['profile_data'] = CustomerSerializer(user.customer_profile).data
            else:
                response_data['user_type'] = 'user'
                response_data['profile_data'] = {}
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    API endpoint for user logout (delete token from database).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: None},
        description="Logout and delete user token from database"
    )
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """
    API endpoint to get and update current user's profile information.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OrganizerSerializer},
        description="Get current user's profile information"
    )
    def get(self, request):
        """Get current user's profile information."""
        # Explicitly check authentication
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = request.user
        
        response_data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        
        # Check if user is an organizer
        if hasattr(user, 'organizer_profile'):
            response_data['user_type'] = 'organizer'
            response_data['profile_data'] = OrganizerSerializer(user.organizer_profile).data
        # Check if user is a customer
        elif hasattr(user, 'customer_profile'):
            response_data['user_type'] = 'customer'
            response_data['profile_data'] = CustomerSerializer(user.customer_profile).data
        else:
            response_data['user_type'] = 'user'
            response_data['profile_data'] = {}
        
        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(
        request=OrganizerSerializer,
        responses={200: OrganizerSerializer},
        description="Partially update current user's profile information"
    )
    def patch(self, request):
        """Partially update current user's profile information."""
        user = request.user
        
        # Update User fields
        user_data = {}
        for field in ['first_name', 'last_name', 'email']:
            if field in request.data:
                user_data[field] = request.data[field]
        
        if user_data:
            for field, value in user_data.items():
                setattr(user, field, value)
            user.save()
        
        # Update profile based on user type
        if hasattr(user, 'organizer_profile'):
            serializer = OrganizerSerializer(user.organizer_profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif hasattr(user, 'customer_profile'):
            serializer = CustomerSerializer(user.customer_profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Return updated profile
        return self.get(request)
