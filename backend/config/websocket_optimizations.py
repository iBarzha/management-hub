import json
import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and implements connection pooling
    """
    
    def __init__(self):
        self.active_connections = defaultdict(set)
        self.user_connections = defaultdict(set)
        self.connection_stats = defaultdict(dict)
        self.message_queues = defaultdict(list)
        self.typing_users = defaultdict(dict)
        
    def add_connection(self, group_name, channel_name, user_id=None):
        self.active_connections[group_name].add(channel_name)
        if user_id:
            self.user_connections[user_id].add(channel_name)
        
        self.connection_stats[channel_name] = {
            'connected_at': timezone.now(),
            'message_count': 0,
            'last_activity': timezone.now()
        }
    
    def remove_connection(self, group_name, channel_name, user_id=None):
        self.active_connections[group_name].discard(channel_name)
        if user_id:
            self.user_connections[user_id].discard(channel_name)
        
        # Clean up stats
        self.connection_stats.pop(channel_name, None)
    
    def get_connection_count(self, group_name):
        return len(self.active_connections[group_name])
    
    def update_activity(self, channel_name):
        if channel_name in self.connection_stats:
            self.connection_stats[channel_name]['last_activity'] = timezone.now()
            self.connection_stats[channel_name]['message_count'] += 1
    
    def get_inactive_connections(self, max_idle_minutes=30):
        """Get connections that have been inactive for too long"""
        cutoff_time = timezone.now() - timedelta(minutes=max_idle_minutes)
        inactive = []
        
        for channel_name, stats in self.connection_stats.items():
            if stats['last_activity'] < cutoff_time:
                inactive.append(channel_name)
        
        return inactive


# Global connection manager
connection_manager = ConnectionManager()


class OptimizedWebsocketMixin:
    """
    Mixin to add performance optimizations to WebSocket consumers
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_message_time = None
        self.message_buffer = []
        self.batch_send_task = None
        
    async def connect(self):
        await super().connect()
        connection_manager.add_connection(
            getattr(self, 'room_group_name', ''),
            self.channel_name,
            getattr(self.scope.get('user'), 'id', None)
        )
    
    async def disconnect(self, close_code):
        await super().disconnect(close_code)
        connection_manager.remove_connection(
            getattr(self, 'room_group_name', ''),
            self.channel_name,
            getattr(self.scope.get('user'), 'id', None)
        )
    
    async def receive(self, text_data):
        connection_manager.update_activity(self.channel_name)
        
        # Rate limiting
        if not await self.check_rate_limit():
            logger.warning(f"Rate limit exceeded for {self.channel_name}")
            return
        
        await super().receive(text_data)
    
    async def check_rate_limit(self, max_messages=10, window_seconds=60):
        """
        Simple rate limiting implementation
        """
        now = timezone.now()
        cache_key = f"ws_rate_limit:{self.channel_name}"
        
        # Get current message count
        messages = cache.get(cache_key, [])
        
        # Remove old messages outside the window
        cutoff_time = now - timedelta(seconds=window_seconds)
        messages = [msg_time for msg_time in messages if msg_time > cutoff_time]
        
        # Check if we're over the limit
        if len(messages) >= max_messages:
            return False
        
        # Add current message
        messages.append(now)
        cache.set(cache_key, messages, window_seconds)
        
        return True
    
    async def batch_send_messages(self, messages, delay=0.1):
        """
        Batch multiple messages together to reduce overhead
        """
        if not messages:
            return
        
        # Wait for a short delay to collect more messages
        await asyncio.sleep(delay)
        
        # Send all messages in batch
        batch_data = {
            'type': 'batch_messages',
            'messages': messages,
            'timestamp': timezone.now().isoformat()
        }
        
        await self.send(text_data=json.dumps(batch_data, cls=DjangoJSONEncoder))
    
    async def handle_typing_debounce(self, user, is_typing, debounce_time=1.0):
        """
        Debounce typing indicators to reduce message spam
        """
        typing_key = f"typing:{self.room_group_name}:{user}"
        
        if is_typing:
            # Set typing status
            connection_manager.typing_users[self.room_group_name][user] = timezone.now()
            
            # Schedule cleanup
            await asyncio.sleep(debounce_time)
            
            # Check if still typing
            last_typing = connection_manager.typing_users[self.room_group_name].get(user)
            if last_typing and (timezone.now() - last_typing).total_seconds() >= debounce_time:
                # User stopped typing
                connection_manager.typing_users[self.room_group_name].pop(user, None)
                await self.send_typing_update(user, False)
        else:
            # User explicitly stopped typing
            connection_manager.typing_users[self.room_group_name].pop(user, None)
            await self.send_typing_update(user, False)
    
    async def send_typing_update(self, user, is_typing):
        """Send typing update to group"""
        pass  # To be implemented by subclasses


class OptimizedChatConsumer(OptimizedWebsocketMixin, AsyncWebsocketConsumer):
    """
    Optimized chat consumer with performance improvements
    """
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Check user authentication
        if not self.scope['user'].is_authenticated:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        await super().connect()
        
        # Cache user join
        await self.cache_user_presence(True)
        
        # Send cached recent messages
        await self.send_recent_messages()
        
        # Broadcast user joined
        await self.broadcast_user_joined()
    
    async def disconnect(self, close_code):
        await super().disconnect(close_code)
        
        # Cache user leave
        await self.cache_user_presence(False)
        
        # Broadcast user left
        await self.broadcast_user_left()
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        await super().receive(text_data)
        
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing_indicator(text_data_json)
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from {self.channel_name}")
            await self.send_error("Invalid message format")
    
    async def handle_chat_message(self, data):
        message = data['message']
        user = self.scope['user']
        
        # Validate message
        if not message.strip() or len(message) > 2000:
            await self.send_error("Invalid message content")
            return
        
        # Save message asynchronously
        chat_message = await self.save_message(user, message)
        
        # Cache the message for quick retrieval
        await self.cache_message(chat_message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': chat_message.id,
                'message': message,
                'user': user.username,
                'user_id': user.id,
                'timestamp': chat_message.created_at.isoformat()
            }
        )
    
    async def handle_typing_indicator(self, data):
        user = self.scope['user']
        is_typing = data.get('is_typing', False)
        
        await self.handle_typing_debounce(user.username, is_typing)
    
    async def send_typing_update(self, user, is_typing):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user': user,
                'is_typing': is_typing
            }
        )
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event.get('message_id'),
            'message': event['message'],
            'user': event['user'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))
    
    async def typing_indicator(self, event):
        if event['user'] != self.scope['user'].username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user': event['user'],
                'is_typing': event['is_typing']
            }))
    
    async def send_error(self, message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    @database_sync_to_async
    def save_message(self, user, message):
        from collaboration.models import ChatMessage
        return ChatMessage.objects.create(
            user=user,
            room=self.room_name,
            message=message
        )
    
    async def cache_message(self, message):
        """Cache recent messages for quick retrieval"""
        cache_key = f"chat_messages:{self.room_name}"
        recent_messages = cache.get(cache_key, [])
        
        message_data = {
            'id': message.id,
            'message': message.message,
            'user': message.user.username,
            'user_id': message.user.id,
            'timestamp': message.created_at.isoformat()
        }
        
        recent_messages.append(message_data)
        
        # Keep only last 50 messages
        if len(recent_messages) > 50:
            recent_messages = recent_messages[-50:]
        
        cache.set(cache_key, recent_messages, 3600)  # Cache for 1 hour
    
    async def send_recent_messages(self):
        """Send recent cached messages to newly connected user"""
        cache_key = f"chat_messages:{self.room_name}"
        recent_messages = cache.get(cache_key, [])
        
        if recent_messages:
            await self.send(text_data=json.dumps({
                'type': 'recent_messages',
                'messages': recent_messages[-20:]  # Send last 20 messages
            }))
    
    async def cache_user_presence(self, is_online):
        """Cache user presence for the room"""
        cache_key = f"room_presence:{self.room_name}"
        online_users = cache.get(cache_key, set())
        
        if is_online:
            online_users.add(self.scope['user'].username)
        else:
            online_users.discard(self.scope['user'].username)
        
        cache.set(cache_key, online_users, 300)  # Cache for 5 minutes
        
        return list(online_users)
    
    async def broadcast_user_joined(self):
        online_users = await self.cache_user_presence(True)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user': self.scope['user'].username,
                'online_users': online_users
            }
        )
    
    async def broadcast_user_left(self):
        online_users = await self.cache_user_presence(False)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user': self.scope['user'].username,
                'online_users': online_users
            }
        )
    
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


# Utility functions for WebSocket optimization
async def cleanup_inactive_connections():
    """Clean up inactive WebSocket connections"""
    inactive_connections = connection_manager.get_inactive_connections()
    logger.info(f"Found {len(inactive_connections)} inactive connections")
    
    # In a real implementation, you'd close these connections
    for channel_name in inactive_connections:
        logger.info(f"Would close inactive connection: {channel_name}")


def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        'total_connections': sum(len(connections) for connections in connection_manager.active_connections.values()),
        'active_groups': len(connection_manager.active_connections),
        'user_connections': len(connection_manager.user_connections),
        'connection_stats': dict(connection_manager.connection_stats)
    }