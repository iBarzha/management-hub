from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/(?P<user_id>\w+)/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/project/(?P<project_id>\w+)/$', consumers.ProjectConsumer.as_asgi()),
]