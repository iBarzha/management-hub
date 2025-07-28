from rest_framework import serializers
from .models import ChatMessage, Notification, UserPresence
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class ChatMessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'room', 'message', 'created_at', 'edited', 'edited_at']
        read_only_fields = ['id', 'user', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message', 'notification_type', 'read', 'created_at', 'project', 'task']
        read_only_fields = ['id', 'user', 'created_at']


class UserPresenceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserPresence
        fields = ['id', 'user', 'is_online', 'last_seen', 'current_project']
        read_only_fields = ['id', 'user', 'last_seen']