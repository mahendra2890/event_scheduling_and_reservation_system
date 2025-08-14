from django.urls import include, path
from rest_framework.routers import DefaultRouter

from user.views import (
    UserViewSet, OrganizerViewSet, CustomerViewSet,
    OrganizerRegistrationView, CustomerRegistrationView,
    LoginView, LogoutView, UserProfileView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'organizers', OrganizerViewSet, basename='organizer')
router.register(r'customers', CustomerViewSet, basename='customer')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/register/organizer/', OrganizerRegistrationView.as_view(), name='organizer-register'),
    path('auth/register/customer/', CustomerRegistrationView.as_view(), name='customer-register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),
]
