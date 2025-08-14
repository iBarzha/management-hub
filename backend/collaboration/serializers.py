from rest_framework import serializers
from .models import ChatMessage, Notification, UserPresence
from django.contrib.auth import get_user_model
from users.validators import CustomValidationMixin, SQLInjectionValidator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class ChatMessageSerializer(CustomValidationMixin, serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'room', 'message', 'created_at', 'edited', 'edited_at']
        read_only_fields = ['id', 'user', 'created_at']
    
    def validate_room(self, value):
        """Validate and sanitize room name."""
        if value:
            SQLInjectionValidator.validate_input(value)
            return self.validate_text_field(value, 'room', max_length=255)
        return value
    
    def validate_message(self, value):
        """Validate and sanitize message content."""
        if value:
            SQLInjectionValidator.validate_input(value)
            return self.validate_html_field(value, 'message', max_length=2000)
        return value


class NotificationSerializer(CustomValidationMixin, serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message', 'notification_type', 'read', 'created_at', 'project', 'task']
        read_only_fields = ['id', 'user', 'created_at']
    
    def validate_title(self, value):
        """Validate and sanitize notification title."""
        if value:
            SQLInjectionValidator.validate_input(value)
            return self.validate_text_field(value, 'title', max_length=255)
        return value
    
    def validate_message(self, value):
        """Validate and sanitize notification message."""
        if value:
            SQLInjectionValidator.validate_input(value)
            return self.validate_text_field(value, 'message', max_length=1000)
        return value


class UserPresenceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserPresence
        fields = ['id', 'user', 'is_online', 'last_seen', 'current_project']
        read_only_fields = ['id', 'user', 'last_seen']