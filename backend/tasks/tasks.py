from celery import shared_task
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import models
from datetime import timedelta
import logging

from .models import Task, TaskComment, TaskAttachment
from projects.models import Project, TeamMember
from config.cache_utils import CacheManager

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_task_assignment(self, task_id, assignee_id, assigner_id):
    """
    Process task assignment and send notifications
    """
    try:
        task = Task.objects.select_related('project', 'assignee', 'created_by').get(id=task_id)
        
        # Send notification email to assignee
        if task.assignee and task.assignee.email:
            send_mail(
                subject=f"New Task Assignment: {task.title}",
                message=f"""
                You have been assigned a new task:
                
                Task: {task.title}
                Project: {task.project.name}
                Priority: {task.get_priority_display()}
                Due Date: {task.due_date or 'Not set'}
                
                Description:
                {task.description}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[task.assignee.email],
                fail_silently=False,
            )
        
        # Invalidate cache
        CacheManager.invalidate_user_cache(assignee_id)
        CacheManager.invalidate_project_cache(task.project.id)
        
        logger.info(f"Processed assignment of task {task.title} to user {assignee_id}")
        return f"Task assignment processed successfully"
        
    except Task.DoesNotExist:
        logger.error(f"Task {task_id} not found")
        return f"Task {task_id} not found"
        
    except Exception as e:
        logger.error(f"Error processing task assignment {task_id}: {str(e)}")
        self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def send_task_deadline_reminders(self):
    """
    Send reminders for tasks approaching deadline
    """
    try:
        tomorrow = timezone.now() + timedelta(days=1)
        
        # Get tasks due tomorrow
        upcoming_tasks = Task.objects.select_related(
            'project', 'assignee'
        ).filter(
            due_date__date=tomorrow.date(),
            status__in=['todo', 'in_progress'],
            assignee__isnull=False
        )
        
        notifications_sent = 0
        
        for task in upcoming_tasks:
            try:
                send_mail(
                    subject=f"Task Deadline Reminder: {task.title}",
                    message=f"""
                    Reminder: Your task is due tomorrow!
                    
                    Task: {task.title}
                    Project: {task.project.name}
                    Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M')}
                    Priority: {task.get_priority_display()}
                    
                    Description:
                    {task.description}
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[task.assignee.email],
                    fail_silently=False,
                )
                notifications_sent += 1
            except Exception as e:
                logger.error(f"Failed to send deadline reminder for task {task.id}: {str(e)}")
        
        logger.info(f"Sent {notifications_sent} deadline reminders")
        return f"Sent {notifications_sent} deadline reminders"
        
    except Exception as e:
        logger.error(f"Error sending deadline reminders: {str(e)}")
        self.retry(countdown=300, exc=e)


@shared_task
def cleanup_old_task_data():
    """
    Clean up old task data and optimize storage
    """
    try:
        # Delete task attachments for completed tasks older than 6 months
        six_months_ago = timezone.now() - timedelta(days=180)
        
        old_completed_tasks = Task.objects.filter(
            status='done',
            updated_at__lt=six_months_ago
        )
        
        # Count attachments to be cleaned
        attachments_count = TaskAttachment.objects.filter(
            task__in=old_completed_tasks
        ).count()
        
        # You might want to move files to archive storage before deletion
        # For now, we'll just log what would be cleaned
        
        logger.info(f"Would clean {attachments_count} old task attachments")
        return f"Cleanup would affect {attachments_count} attachments"
        
    except Exception as e:
        logger.error(f"Error during task data cleanup: {str(e)}")
        return f"Cleanup failed: {str(e)}"


@shared_task(bind=True, max_retries=3)
def bulk_update_task_status(self, task_ids, new_status, user_id):
    """
    Bulk update task statuses
    """
    try:
        updated_count = 0
        
        for task_id in task_ids:
            try:
                task = Task.objects.get(id=task_id)
                task.status = new_status
                task.save()
                updated_count += 1
                
                # Invalidate cache for the task's project
                CacheManager.invalidate_project_cache(task.project.id)
                
            except Task.DoesNotExist:
                logger.warning(f"Task {task_id} not found for bulk update")
                continue
        
        # Invalidate user cache
        CacheManager.invalidate_user_cache(user_id)
        
        logger.info(f"Bulk updated {updated_count} tasks to status {new_status}")
        return f"Updated {updated_count} tasks"
        
    except Exception as e:
        logger.error(f"Error in bulk task update: {str(e)}")
        self.retry(countdown=60, exc=e)


@shared_task
def generate_task_analytics():
    """
    Generate task analytics data for dashboard
    """
    try:
        from django.db.models import Count, Avg
        
        # Generate various task statistics
        stats = Task.objects.aggregate(
            total_tasks=Count('id'),
            avg_completion_time=Avg('actual_hours'),
            overdue_tasks=Count('id', filter=models.Q(
                due_date__lt=timezone.now(),
                status__in=['todo', 'in_progress']
            ))
        )
        
        # Cache the results
        cache.set('task_analytics', stats, 3600)  # Cache for 1 hour
        
        logger.info("Generated task analytics")
        return stats
        
    except Exception as e:
        logger.error(f"Error generating task analytics: {str(e)}")
        return {'error': str(e)}


@shared_task(bind=True, max_retries=2)
def process_task_comment_notifications(self, comment_id):
    """
    Process notifications for new task comments
    """
    try:
        comment = TaskComment.objects.select_related(
            'task', 'task__project', 'task__assignee', 'author'
        ).get(id=comment_id)
        
        # Notify task assignee if they're not the commenter
        recipients = []
        
        if comment.task.assignee and comment.task.assignee != comment.author:
            recipients.append(comment.task.assignee.email)
        
        # Notify project team members who have commented on this task
        other_commenters = TaskComment.objects.filter(
            task=comment.task
        ).exclude(
            author=comment.author
        ).select_related('author').distinct()
        
        for commenter in other_commenters:
            if commenter.author.email not in recipients:
                recipients.append(commenter.author.email)
        
        if recipients:
            send_mail(
                subject=f"New comment on task: {comment.task.title}",
                message=f"""
                {comment.author.get_full_name() or comment.author.username} commented on the task "{comment.task.title}":
                
                {comment.content}
                
                Project: {comment.task.project.name}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
        
        logger.info(f"Sent comment notifications to {len(recipients)} recipients")
        return f"Sent notifications to {len(recipients)} recipients"
        
    except TaskComment.DoesNotExist:
        logger.error(f"Task comment {comment_id} not found")
        return f"Comment {comment_id} not found"
        
    except Exception as e:
        logger.error(f"Error processing comment notifications: {str(e)}")
        self.retry(countdown=60, exc=e)