import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Add user to room and broadcast presence
        await self.add_user_to_room()
        await self.broadcast_user_joined()

    async def disconnect(self, close_code):
        # Remove user from room and broadcast presence
        await self.remove_user_from_room()
        await self.broadcast_user_left()
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            message = text_data_json['message']
            user = self.scope['user']
            
            # Save message to database
            chat_message = await self.save_message(user, message)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user': user.username,
                    'user_id': user.id,
                    'timestamp': chat_message.created_at.isoformat()
                }
            )
        elif message_type == 'typing':
            # Handle typing indicators
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user': self.scope['user'].username,
                    'is_typing': text_data_json.get('is_typing', False)
                }
            )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'user': event['user'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))

    async def typing_indicator(self, event):
        # Send typing indicator to WebSocket
        if event['user'] != self.scope['user'].username:  # Don't send to sender
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user': event['user'],
                'is_typing': event['is_typing']
            }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user': event['user'],
            'online_users': event['online_users']
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user': event['user'],
            'online_users': event['online_users']
        }))

    @database_sync_to_async
    def save_message(self, user, message):
        from .models import ChatMessage
        return ChatMessage.objects.create(
            user=user,
            room=self.room_name,
            message=message
        )

    @database_sync_to_async
    def add_user_to_room(self):
        from .models import RoomParticipant
        RoomParticipant.objects.get_or_create(
            room=self.room_name,
            user=self.scope['user']
        )

    @database_sync_to_async
    def remove_user_from_room(self):
        from .models import RoomParticipant
        RoomParticipant.objects.filter(
            room=self.room_name,
            user=self.scope['user']
        ).delete()

    @database_sync_to_async
    def get_online_users(self):
        from .models import RoomParticipant
        participants = RoomParticipant.objects.filter(room=self.room_name).select_related('user')
        return [p.user.username for p in participants]

    async def broadcast_user_joined(self):
        online_users = await self.get_online_users()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user': self.scope['user'].username,
                'online_users': online_users
            }
        )

    async def broadcast_user_left(self):
        online_users = await self.get_online_users()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user': self.scope['user'].username,
                'online_users': online_users
            }
        )


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user_group_name = f'notifications_{self.user_id}'
        
        # Join user notification group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave user notification group
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def notification(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['title'],
            'message': event['message'],
            'notification_type': event.get('notification_type', 'info'),
            'timestamp': event['timestamp']
        }, cls=DjangoJSONEncoder))


class ProjectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.project_group_name = f'project_{self.project_id}'
        
        # Join project group
        await self.channel_layer.group_add(
            self.project_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave project group
        await self.channel_layer.group_discard(
            self.project_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'task_update':
            # Handle collaborative task updates
            await self.channel_layer.group_send(
                self.project_group_name,
                {
                    'type': 'task_updated',
                    'task_id': text_data_json['task_id'],
                    'updates': text_data_json['updates'],
                    'user': self.scope['user'].username,
                    'timestamp': text_data_json.get('timestamp')
                }
            )

    async def task_updated(self, event):
        # Send task update to WebSocket (except to sender)
        if event.get('user') != self.scope['user'].username:
            await self.send(text_data=json.dumps({
                'type': 'task_updated',
                'task_id': event['task_id'],
                'updates': event['updates'],
                'user': event['user'],
                'timestamp': event['timestamp']
            }, cls=DjangoJSONEncoder))

    async def project_updated(self, event):
        # Send project update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'project_updated',
            'project_id': event['project_id'],
            'updates': event['updates'],
            'user': event['user'],
            'timestamp': event['timestamp']
        }, cls=DjangoJSONEncoder))