from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ChatMessage, Notification, UserPresence
from .serializers import ChatMessageSerializer, NotificationSerializer, UserPresenceSerializer


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        room = self.request.query_params.get('room')
        if room:
            return ChatMessage.objects.filter(room=room)
        return ChatMessage.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({'status': 'success'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'status': 'success'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, read=False).count()
        return Response({'count': count})


class UserPresenceViewSet(viewsets.ModelViewSet):
    serializer_class = UserPresenceSerializer
    permission_classes = [IsAuthenticated]
    queryset = UserPresence.objects.all()
    
    @action(detail=False, methods=['post'])
    def update_presence(self, request):
        presence, created = UserPresence.objects.get_or_create(user=request.user)
        presence.is_online = request.data.get('is_online', True)
        presence.current_project_id = request.data.get('current_project')
        presence.save()
        
        serializer = self.get_serializer(presence)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def online_users(self, request):
        project_id = request.query_params.get('project_id')
        queryset = UserPresence.objects.filter(is_online=True)
        
        if project_id:
            queryset = queryset.filter(current_project_id=project_id)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


def send_notification(user_id, title, message, notification_type='info', project_id=None, task_id=None):
    """
    Utility function to send real-time notifications
    """
    # Create notification in database
    notification = Notification.objects.create(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        project_id=project_id,
        task_id=task_id
    )
    
    # Send real-time notification via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{user_id}',
        {
            'type': 'notification',
            'title': title,
            'message': message,
            'notification_type': notification_type,
            'timestamp': notification.created_at.isoformat()
        }
    )
    
    return notification
