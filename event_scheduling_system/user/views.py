from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, OpenApiExample

from user.serializers import (
    OrganizerSerializer, CustomerSerializer,
    OrganizerRegistrationSerializer, CustomerRegistrationSerializer,
    LoginSerializer, HistoryPointSerializer
)
from user.models import Organizer, Customer, HistoryPoint


class HistoryPointViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing history points.
    Users can only view their own history points.
    """
    serializer_class = HistoryPointSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Users can only see their own history points.
        """
        return HistoryPoint.objects.filter(user=self.request.user).select_related(
            'user', 'content_type'
        )
    
    def list(self, request, *args, **kwargs):
        """
        List user's history points with optional filtering.
        """
        queryset = self.get_queryset()
        
        # Filter by action type
        action = request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by content type
        content_type = request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type__model=content_type)
        
        # Filter by date range
        start_date = request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        
        end_date = request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BaseRegistrationView(APIView):
    """
    Base class for registration views to eliminate code duplication.
    """
    permission_classes = [AllowAny]
    
    def _handle_registration(self, request, serializer_class, user_type):
        """
        Common registration logic for both organizer and customer registration.
        """
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            token, created = Token.objects.get_or_create(user=profile.user)
            
            # Log the registration action
            HistoryPoint.log_action(
                user=profile.user,
                action=HistoryPoint.ACTION_REGISTER,
                obj=profile,
                details={
                    'user_type': user_type,
                    'email': profile.user.email,
                    **self._get_additional_details(profile, user_type)
                }
            )
            
            return Response({
                'message': f'{user_type.title()} registered successfully',
                f'{user_type}_id': profile.id,
                'username': profile.user.username,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_additional_details(self, profile, user_type):
        """
        Get additional details for logging based on user type.
        """
        if user_type == 'organizer':
            return {'organization_name': profile.organization_name}
        return {}


class OrganizerRegistrationView(BaseRegistrationView):
    """
    API endpoint for Organizer registration. Only allow POST requests.
    """
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
        return self._handle_registration(request, OrganizerRegistrationSerializer, 'organizer')


class CustomerRegistrationView(BaseRegistrationView):
    """
    API endpoint for Customer registration. Only allow POST requests.
    """
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
        return self._handle_registration(request, CustomerRegistrationSerializer, 'customer')


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
            
            # Log the login action
            HistoryPoint.log_action(
                user=user,
                action=HistoryPoint.ACTION_LOGIN,
                obj=user,
                details={
                    'token_created': created,
                    'login_method': 'username_password'
                }
            )
            
            # Build response data
            response_data = self._build_user_response(user, token.key)
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _build_user_response(self, user, token_key):
        """
        Build response data based on user type.
        """
        response_data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'token': token_key
        }
        
        # Determine user type and add profile data
        if hasattr(user, 'organizer_profile'):
            response_data['user_type'] = 'organizer'
            response_data['profile_data'] = OrganizerSerializer(user.organizer_profile).data
        elif hasattr(user, 'customer_profile'):
            response_data['user_type'] = 'customer'
            response_data['profile_data'] = CustomerSerializer(user.customer_profile).data
        else:
            response_data['user_type'] = 'user'
            response_data['profile_data'] = {}
        
        return response_data


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
        # Log the logout action before deleting token
        HistoryPoint.log_action(
            user=request.user,
            action=HistoryPoint.ACTION_LOGOUT,
            obj=request.user,
            details={
                'logout_method': 'token_deletion'
            }
        )
        
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
        # Build response data using the same helper as LoginView
        response_data = self._build_user_response(request.user)
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _build_user_response(self, user):
        """
        Build response data based on user type.
        """
        response_data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        
        # Determine user type and add profile data
        if hasattr(user, 'organizer_profile'):
            response_data['user_type'] = 'organizer'
            response_data['profile_data'] = OrganizerSerializer(user.organizer_profile).data
        elif hasattr(user, 'customer_profile'):
            response_data['user_type'] = 'customer'
            response_data['profile_data'] = CustomerSerializer(user.customer_profile).data
        else:
            response_data['user_type'] = 'user'
            response_data['profile_data'] = {}
        
        return response_data