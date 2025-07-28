from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatMessageViewSet, NotificationViewSet, UserPresenceViewSet

router = DefaultRouter()
router.register(r'messages', ChatMessageViewSet, basename='chatmessage')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'presence', UserPresenceViewSet, basename='userpresence')

urlpatterns = [
    path('', include(router.urls)),
]