from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_websocket_data():
    """
    Clean up old WebSocket-related data from cache
    """
    try:
        # Clean up old typing indicators
        typing_pattern = "typing:*"
        typing_keys = cache.keys(typing_pattern)
        if typing_keys:
            cache.delete_many(typing_keys)
            logger.info(f"Cleaned up {len(typing_keys)} typing indicators")
        
        # Clean up old presence data
        presence_pattern = "room_presence:*"
        presence_keys = cache.keys(presence_pattern)
        cleaned_presence = 0
        
        for key in presence_keys:
            # Check if presence data is stale (older than 5 minutes)
            presence_data = cache.get(key)
            if presence_data is None:
                cleaned_presence += 1
        
        logger.info(f"Processed {len(presence_keys)} presence entries")
        
        # Clean up old chat message caches (keep last 24 hours)
        chat_pattern = "chat_messages:*"
        chat_keys = cache.keys(chat_pattern)
        
        for key in chat_keys:
            messages = cache.get(key, [])
            if messages:
                # Keep only messages from last 24 hours
                cutoff_time = timezone.now() - timedelta(hours=24)
                recent_messages = []
                
                for msg in messages:
                    try:
                        msg_time = timezone.datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                        if msg_time > cutoff_time:
                            recent_messages.append(msg)
                    except (KeyError, ValueError):
                        continue
                
                if len(recent_messages) != len(messages):
                    cache.set(key, recent_messages, 3600)
        
        logger.info(f"Processed {len(chat_keys)} chat message caches")
        
        return {
            'typing_indicators_cleaned': len(typing_keys) if typing_keys else 0,
            'presence_entries_processed': len(presence_keys),
            'chat_caches_processed': len(chat_keys)
        }
        
    except Exception as e:
        logger.error(f"Error during WebSocket cleanup: {str(e)}")
        return {'error': str(e)}


@shared_task
def websocket_health_check():
    """
    Perform health check on WebSocket infrastructure
    """
    try:
        from config.websocket_optimizations import get_websocket_stats
        
        stats = get_websocket_stats()
        
        # Log statistics
        logger.info(f"WebSocket Stats: {stats}")
        
        # Check for issues
        issues = []
        
        # Check for too many connections
        if stats['total_connections'] > 1000:
            issues.append("High connection count")
        
        # Check for inactive connections
        if stats.get('inactive_connections', 0) > 50:
            issues.append("Many inactive connections")
        
        # Store stats in cache for monitoring
        cache.set('websocket_health_stats', {
            'timestamp': timezone.now().isoformat(),
            'stats': stats,
            'issues': issues
        }, 300)
        
        return {
            'status': 'healthy' if not issues else 'warning',
            'stats': stats,
            'issues': issues
        }
        
    except Exception as e:
        logger.error(f"WebSocket health check failed: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3)
def broadcast_system_notification(self, notification_data):
    """
    Broadcast system notification to all connected users
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        
        # Broadcast to all notification groups
        # This is a simplified approach - in production you'd want to be more selective
        async_to_sync(channel_layer.group_send)(
            "system_notifications",
            {
                'type': 'system_notification',
                'title': notification_data.get('title', 'System Notification'),
                'message': notification_data.get('message', ''),
                'level': notification_data.get('level', 'info'),
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.info("Broadcasted system notification to all users")
        return "System notification broadcasted successfully"
        
    except Exception as e:
        logger.error(f"Error broadcasting system notification: {str(e)}")
        self.retry(countdown=60, exc=e)


@shared_task
def generate_websocket_metrics():
    """
    Generate WebSocket usage metrics
    """
    try:
        from config.websocket_optimizations import connection_manager
        
        # Calculate metrics
        total_connections = sum(
            len(connections) for connections in connection_manager.active_connections.values()
        )
        
        active_rooms = len(connection_manager.active_connections)
        
        # Message activity metrics
        total_messages = sum(
            stats.get('message_count', 0) 
            for stats in connection_manager.connection_stats.values()
        )
        
        # Average connection duration
        now = timezone.now()
        connection_durations = []
        
        for stats in connection_manager.connection_stats.values():
            duration = (now - stats['connected_at']).total_seconds() / 60  # in minutes
            connection_durations.append(duration)
        
        avg_duration = sum(connection_durations) / len(connection_durations) if connection_durations else 0
        
        metrics = {
            'timestamp': now.isoformat(),
            'total_connections': total_connections,
            'active_rooms': active_rooms,
            'total_messages': total_messages,
            'average_connection_duration_minutes': round(avg_duration, 2),
            'peak_connections': max(len(connections) for connections in connection_manager.active_connections.values()) if connection_manager.active_connections else 0
        }
        
        # Cache metrics for dashboard
        cache.set('websocket_metrics', metrics, 300)
        
        logger.info(f"Generated WebSocket metrics: {metrics}")
        return metrics
        
    except Exception as e:
        logger.error(f"Error generating WebSocket metrics: {str(e)}")
        return {'error': str(e)}


@shared_task
def optimize_message_history():
    """
    Optimize message history storage
    """
    try:
        from .models import ChatMessage
        
        # Archive old messages (older than 90 days)
        archive_date = timezone.now() - timedelta(days=90)
        
        old_messages_count = ChatMessage.objects.filter(
            created_at__lt=archive_date
        ).count()
        
        # In production, you might move these to an archive table
        # For now, we'll just count them
        
        # Clean up very old messages (older than 1 year)
        cleanup_date = timezone.now() - timedelta(days=365)
        
        very_old_count = ChatMessage.objects.filter(
            created_at__lt=cleanup_date
        ).count()
        
        # You might want to actually delete these in production
        # ChatMessage.objects.filter(created_at__lt=cleanup_date).delete()
        
        logger.info(f"Found {old_messages_count} messages to archive, {very_old_count} very old messages")
        
        return {
            'messages_to_archive': old_messages_count,
            'very_old_messages': very_old_count,
            'status': 'completed'
        }
        
    except Exception as e:
        logger.error(f"Error optimizing message history: {str(e)}")
        return {'error': str(e)}