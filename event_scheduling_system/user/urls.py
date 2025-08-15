from django.urls import include, path
from rest_framework.routers import DefaultRouter

from user.views import (
    OrganizerRegistrationView, CustomerRegistrationView,
    LoginView, LogoutView, UserProfileView, HistoryPointViewSet
)

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'history', HistoryPointViewSet, basename='history')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/organizer/', OrganizerRegistrationView.as_view(), name='organizer-register'),
    path('auth/register/customer/', CustomerRegistrationView.as_view(), name='customer-register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Include router URLs
    path('', include(router.urls)),
]
