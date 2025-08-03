"""
Discord notification service for sending project management notifications
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from django.conf import settings
from asgiref.sync import sync_to_async

from .models import DiscordIntegration, DiscordChannel
from .discord_bot import bot_manager

logger = logging.getLogger(__name__)


class DiscordNotificationService:
    """Service for sending Discord notifications"""
    
    @staticmethod
    async def send_task_notification(task, event_type: str, user=None):
        """Send task-related notification to Discord"""
        try:
            # Get project Discord channels
            channels = await sync_to_async(list)(
                DiscordChannel.objects.filter(
                    project=task.project,
                    notifications_enabled=True,
                    notification_types__contains=[event_type]
                ).select_related('integration')
            )
            
            if not channels:
                return
            
            # Prepare embed data
            embed_data = await DiscordNotificationService._prepare_task_embed(task, event_type, user)
            
            # Send to each channel
            for channel in channels:
                try:
                    success = await bot_manager.send_notification(channel.channel_id, embed_data)
                    if success:
                        logger.info(f"Sent Discord notification to channel {channel.channel_name}")
                    else:
                        logger.warning(f"Failed to send Discord notification to channel {channel.channel_name}")
                except Exception as e:
                    logger.error(f"Error sending Discord notification: {e}")
                    
        except Exception as e:
            logger.error(f"Error in Discord task notification: {e}")
    
    @staticmethod
    async def send_project_notification(project, event_type: str, user=None):
        """Send project-related notification to Discord"""
        try:
            # Get project Discord channels
            channels = await sync_to_async(list)(
                DiscordChannel.objects.filter(
                    project=project,
                    notifications_enabled=True,
                    notification_types__contains=[event_type]
                ).select_related('integration')
            )
            
            if not channels:
                return
            
            # Prepare embed data
            embed_data = await DiscordNotificationService._prepare_project_embed(project, event_type, user)
            
            # Send to each channel
            for channel in channels:
                try:
                    success = await bot_manager.send_notification(channel.channel_id, embed_data)
                    if success:
                        logger.info(f"Sent Discord notification to channel {channel.channel_name}")
                    else:
                        logger.warning(f"Failed to send Discord notification to channel {channel.channel_name}")
                except Exception as e:
                    logger.error(f"Error sending Discord notification: {e}")
                    
        except Exception as e:
            logger.error(f"Error in Discord project notification: {e}")
    
    @staticmethod
    async def send_deadline_reminder(task):
        """Send deadline reminder notification"""
        try:
            channels = await sync_to_async(list)(
                DiscordChannel.objects.filter(
                    project=task.project,
                    notifications_enabled=True,
                    notification_types__contains=['deadline_reminder']
                ).select_related('integration')
            )
            
            if not channels:
                return
            
            # Calculate time until deadline
            time_until = task.due_date - datetime.now(task.due_date.tzinfo)
            days_until = time_until.days
            hours_until = time_until.seconds // 3600
            
            if days_until > 0:
                time_str = f"{days_until} day(s)"
            elif hours_until > 0:
                time_str = f"{hours_until} hour(s)"
            else:
                time_str = "less than 1 hour"
            
            embed_data = {
                'title': '⏰ Deadline Reminder',
                'description': f"**{task.title}** is due in {time_str}",
                'color': 0xff6b35,  # Orange
                'fields': [
                    {'name': 'Project', 'value': task.project.name, 'inline': True},
                    {'name': 'Assignee', 'value': task.assignee.get_full_name() if task.assignee else 'Unassigned', 'inline': True},
                    {'name': 'Priority', 'value': task.priority.title(), 'inline': True},
                    {'name': 'Status', 'value': task.status.title().replace('_', ' '), 'inline': True},
                    {'name': 'Due Date', 'value': task.due_date.strftime('%Y-%m-%d %H:%M'), 'inline': True},
                ],
                'timestamp': datetime.utcnow().isoformat(),
                'footer': {'text': 'Project Management Hub'}
            }
            
            # Send to each channel
            for channel in channels:
                try:
                    success = await bot_manager.send_notification(channel.channel_id, embed_data)
                    if success:
                        logger.info(f"Sent deadline reminder to Discord channel {channel.channel_name}")
                except Exception as e:
                    logger.error(f"Error sending deadline reminder: {e}")
                    
        except Exception as e:
            logger.error(f"Error in Discord deadline reminder: {e}")
    
    @staticmethod
    async def send_daily_standup_reminder(project):
        """Send daily standup reminder"""
        try:
            channels = await sync_to_async(list)(
                DiscordChannel.objects.filter(
                    project=project,
                    notifications_enabled=True,
                    notification_types__contains=['standup_reminder']
                ).select_related('integration')
            )
            
            if not channels:
                return
            
            embed_data = {
                'title': '🗣️ Daily Standup Reminder',
                'description': f"Time for the daily standup for **{project.name}**!",
                'color': 0x4285f4,  # Blue
                'fields': [
                    {
                        'name': 'What to share:',
                        'value': '• What did you accomplish yesterday?\n• What will you work on today?\n• Are there any blockers?',
                        'inline': False
                    }
                ],
                'timestamp': datetime.utcnow().isoformat(),
                'footer': {'text': 'Project Management Hub'}
            }
            
            # Send to each channel
            for channel in channels:
                try:
                    success = await bot_manager.send_notification(channel.channel_id, embed_data)
                    if success:
                        logger.info(f"Sent standup reminder to Discord channel {channel.channel_name}")
                except Exception as e:
                    logger.error(f"Error sending standup reminder: {e}")
                    
        except Exception as e:
            logger.error(f"Error in Discord standup reminder: {e}")
    
    @staticmethod
    async def _prepare_task_embed(task, event_type: str, user=None) -> Dict[str, Any]:
        """Prepare embed data for task notifications"""
        # Color mapping for different events
        color_map = {
            'task_created': 0x28a745,     # Green
            'task_updated': 0x17a2b8,     # Blue
            'task_assigned': 0xffc107,    # Yellow
            'task_completed': 0x6f42c1,   # Purple
            'task_deleted': 0xdc3545,     # Red
        }
        
        # Title mapping
        title_map = {
            'task_created': '✅ Task Created',
            'task_updated': '📝 Task Updated',
            'task_assigned': '👤 Task Assigned',
            'task_completed': '🎉 Task Completed',
            'task_deleted': '🗑️ Task Deleted',
        }
        
        # Priority emojis
        priority_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴',
            'urgent': '🚨'
        }
        
        embed_data = {
            'title': title_map.get(event_type, '📋 Task Update'),
            'description': f"{priority_emoji.get(task.priority, '⚪')} **{task.title}**",
            'color': color_map.get(event_type, 0x6c757d),
            'fields': [
                {'name': 'Project', 'value': task.project.name, 'inline': True},
                {'name': 'Status', 'value': task.status.title().replace('_', ' '), 'inline': True},
                {'name': 'Priority', 'value': task.priority.title(), 'inline': True},
            ],
            'timestamp': datetime.utcnow().isoformat(),
            'footer': {'text': 'Project Management Hub'}
        }
        
        # Add assignee field
        if task.assignee:
            embed_data['fields'].append({
                'name': 'Assignee',
                'value': task.assignee.get_full_name(),
                'inline': True
            })
        
        # Add due date if exists
        if task.due_date:
            embed_data['fields'].append({
                'name': 'Due Date',
                'value': task.due_date.strftime('%Y-%m-%d'),
                'inline': True
            })
        
        # Add user who triggered the event
        if user:
            embed_data['fields'].append({
                'name': 'Updated by',
                'value': user.get_full_name(),
                'inline': True
            })
        
        # Add description if it exists and isn't too long
        if task.description and len(task.description) <= 200:
            embed_data['fields'].append({
                'name': 'Description',
                'value': task.description,
                'inline': False
            })
        
        return embed_data
    
    @staticmethod
    async def _prepare_project_embed(project, event_type: str, user=None) -> Dict[str, Any]:
        """Prepare embed data for project notifications"""
        # Color mapping for different events
        color_map = {
            'project_created': 0x28a745,     # Green
            'project_updated': 0x17a2b8,     # Blue
            'project_completed': 0x6f42c1,   # Purple
            'project_archived': 0x6c757d,    # Gray
        }
        
        # Title mapping
        title_map = {
            'project_created': '🚀 Project Created',
            'project_updated': '📊 Project Updated',
            'project_completed': '🎯 Project Completed',
            'project_archived': '📦 Project Archived',
        }
        
        embed_data = {
            'title': title_map.get(event_type, '📋 Project Update'),
            'description': f"**{project.name}**",
            'color': color_map.get(event_type, 0x6c757d),
            'fields': [
                {'name': 'Status', 'value': project.status.title().replace('_', ' '), 'inline': True},
                {'name': 'Team', 'value': project.team.name, 'inline': True},
            ],
            'timestamp': datetime.utcnow().isoformat(),
            'footer': {'text': 'Project Management Hub'}
        }
        
        # Add dates
        if project.start_date:
            embed_data['fields'].append({
                'name': 'Start Date',
                'value': project.start_date.strftime('%Y-%m-%d'),
                'inline': True
            })
        
        if project.end_date:
            embed_data['fields'].append({
                'name': 'End Date',
                'value': project.end_date.strftime('%Y-%m-%d'),
                'inline': True
            })
        
        # Add user who triggered the event
        if user:
            embed_data['fields'].append({
                'name': 'Updated by',
                'value': user.get_full_name(),
                'inline': True
            })
        
        # Add description if it exists and isn't too long
        if project.description and len(project.description) <= 200:
            embed_data['fields'].append({
                'name': 'Description',
                'value': project.description,
                'inline': False
            })
        
        return embed_data


# Synchronous wrapper functions for Django signals
def send_task_notification_sync(task, event_type: str, user=None):
    """Synchronous wrapper for task notifications"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a task
            asyncio.create_task(
                DiscordNotificationService.send_task_notification(task, event_type, user)
            )
        else:
            # If we're in sync context, run the async function
            loop.run_until_complete(
                DiscordNotificationService.send_task_notification(task, event_type, user)
            )
    except Exception as e:
        logger.error(f"Error in sync task notification wrapper: {e}")


def send_project_notification_sync(project, event_type: str, user=None):
    """Synchronous wrapper for project notifications"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a task
            asyncio.create_task(
                DiscordNotificationService.send_project_notification(project, event_type, user)
            )
        else:
            # If we're in sync context, run the async function
            loop.run_until_complete(
                DiscordNotificationService.send_project_notification(project, event_type, user)
            )
    except Exception as e:
        logger.error(f"Error in sync project notification wrapper: {e}")


def send_deadline_reminder_sync(task):
    """Synchronous wrapper for deadline reminders"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(
                DiscordNotificationService.send_deadline_reminder(task)
            )
        else:
            loop.run_until_complete(
                DiscordNotificationService.send_deadline_reminder(task)
            )
    except Exception as e:
        logger.error(f"Error in sync deadline reminder wrapper: {e}")


def send_daily_standup_reminder_sync(project):
    """Synchronous wrapper for standup reminders"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(
                DiscordNotificationService.send_daily_standup_reminder(project)
            )
        else:
            loop.run_until_complete(
                DiscordNotificationService.send_daily_standup_reminder(project)
            )
    except Exception as e:
        logger.error(f"Error in sync standup reminder wrapper: {e}")