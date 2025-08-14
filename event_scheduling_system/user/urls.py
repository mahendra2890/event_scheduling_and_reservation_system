from django.urls import include, path

from user.views import UserViewSet

urlpatterns = [
    path('users/', UserViewSet.as_view({'get': 'retrieve', 'post': 'create', 'patch': 'partial_update', 'delete': 'destroy'}), name='user-list'),
    
]
