from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from user.serializers import (
    UserSerializer, OrganizerSerializer, CustomerSerializer,
    OrganizerRegistrationSerializer, CustomerRegistrationSerializer,
    LoginSerializer, UserTypeResponseSerializer
)
from user.models import Organizer, Customer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to view and edit their own profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own user profile
        return User.objects.filter(id=self.request.user.id)

    def perform_update(self, serializer):
        # Ensure only the owner can update
        if serializer.instance.id != self.request.user.id:
            raise permissions.PermissionDenied("You can only update your own profile")
        serializer.save()


class OrganizerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Organizer CRUD operations.
    """
    serializer_class = OrganizerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own organizer profile
        if hasattr(self.request.user, 'organizer_profile'):
            return Organizer.objects.filter(user=self.request.user)
        return Organizer.objects.none()

    def perform_create(self, serializer):
        # Ensure the organizer is created for the current user
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Ensure only the owner can update
        if serializer.instance.user != self.request.user:
            raise permissions.PermissionDenied("You can only update your own profile")
        serializer.save()


class CustomerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Customer CRUD operations.
    """
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own customer profile
        if hasattr(self.request.user, 'customer_profile'):
            return Customer.objects.filter(user=self.request.user)
        return Customer.objects.none()

    def perform_create(self, serializer):
        # Ensure the customer is created for the current user
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Ensure only the owner can update
        if serializer.instance.user != self.request.user:
            raise permissions.PermissionDenied("You can only update your own profile")
        serializer.save()


class OrganizerRegistrationView(APIView):
    """
    API endpoint for Organizer registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OrganizerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            organizer = serializer.save()
            return Response({
                'message': 'Organizer registered successfully',
                'organizer_id': organizer.id,
                'username': organizer.user.username
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerRegistrationView(APIView):
    """
    API endpoint for Customer registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            return Response({
                'message': 'Customer registered successfully',
                'customer_id': customer.id,
                'username': customer.user.username
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    API endpoint for user login.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            
            # Determine user type and return appropriate data
            response_data = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
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
    API endpoint for user logout.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """
    API endpoint to get current user's profile information.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
