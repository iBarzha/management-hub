from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'avatar', 'bio', 'timezone',
                  'notification_preferences', 'is_online', 'last_seen', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_online', 'last_seen']


class UserPreferencesSerializer(serializers.ModelSerializer):
    email_notifications = serializers.JSONField(required=False)
    
    class Meta:
        model = User
        fields = ['notification_preferences']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Provide default email notification settings if not set
        default_email_settings = {
            'enabled': True,
            'task_assignments': True,
            'task_updates': False,
            'project_updates': True,
            'deadline_reminders': True,
            'mentions': True,
            'comments': False,
            'other': False
        }
        
        if not data['notification_preferences']:
            data['notification_preferences'] = {}
            
        if 'email_notifications' not in data['notification_preferences']:
            data['notification_preferences']['email_notifications'] = default_email_settings
            
        # Add email_notifications to root level for easier access
        data['email_notifications'] = data['notification_preferences'].get('email_notifications', default_email_settings)
        
        return data
        
    def update(self, instance, validated_data):
        notification_prefs = validated_data.get('notification_preferences', {})
        
        # Merge with existing preferences
        if not instance.notification_preferences:
            instance.notification_preferences = {}
            
        instance.notification_preferences.update(notification_prefs)
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user