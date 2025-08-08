from celery import shared_task
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Project, Team, TeamMember
from tasks.models import Task
from config.cache_utils import CacheManager

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def refresh_project_metrics(self, project_id):
    """
    Background task to refresh project metrics
    """
    try:
        from analytics.services import MetricsCalculationService
        
        project = Project.objects.get(id=project_id)
        
        # Calculate fresh metrics
        metrics = MetricsCalculationService.calculate_project_metrics(project)
        
        # Invalidate related cache
        CacheManager.invalidate_project_cache(project_id)
        
        logger.info(f"Successfully refreshed metrics for project {project.name}")
        return f"Metrics refreshed for project {project.name}"
        
    except Project.DoesNotExist:
        logger.error(f"Project with id {project_id} not found")
        return f"Project {project_id} not found"
        
    except Exception as e:
        logger.error(f"Error refreshing metrics for project {project_id}: {str(e)}")
        self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def send_project_notification(self, project_id, notification_type, message, recipient_ids=None):
    """
    Send notifications to project team members
    """
    try:
        project = Project.objects.select_related('team').get(id=project_id)
        
        if recipient_ids:
            recipients = TeamMember.objects.filter(
                team=project.team, 
                user_id__in=recipient_ids
            ).select_related('user')
        else:
            recipients = TeamMember.objects.filter(
                team=project.team
            ).select_related('user')
        
        emails_sent = 0
        for member in recipients:
            try:
                send_mail(
                    subject=f"Project Update: {project.name}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[member.user.email],
                    fail_silently=False,
                )
                emails_sent += 1
            except Exception as e:
                logger.error(f"Failed to send email to {member.user.email}: {str(e)}")
        
        logger.info(f"Sent {emails_sent} notifications for project {project.name}")
        return f"Sent {emails_sent} notifications"
        
    except Project.DoesNotExist:
        logger.error(f"Project with id {project_id} not found")
        return f"Project {project_id} not found"
        
    except Exception as e:
        logger.error(f"Error sending notifications for project {project_id}: {str(e)}")
        self.retry(countdown=30, exc=e)


@shared_task
def cleanup_expired_cache():
    """
    Cleanup expired cache entries
    """
    try:
        # This is handled by Redis TTL, but we can add custom cleanup logic here
        logger.info("Cache cleanup task completed")
        return "Cache cleanup completed"
    except Exception as e:
        logger.error(f"Error during cache cleanup: {str(e)}")
        return f"Cache cleanup failed: {str(e)}"


@shared_task
def generate_project_reports_batch(project_ids, report_type='summary'):
    """
    Generate reports for multiple projects in batch
    """
    try:
        from analytics.services import ReportService
        
        results = []
        for project_id in project_ids:
            try:
                project = Project.objects.get(id=project_id)
                report_data = ReportService.generate_project_summary_data(
                    project, 
                    timezone.now() - timedelta(days=30), 
                    timezone.now()
                )
                results.append({
                    'project_id': project_id,
                    'status': 'success',
                    'data': report_data
                })
            except Exception as e:
                results.append({
                    'project_id': project_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        logger.info(f"Generated reports for {len(results)} projects")
        return results
        
    except Exception as e:
        logger.error(f"Batch report generation failed: {str(e)}")
        return {'error': str(e)}


@shared_task(bind=True, max_retries=2)
def optimize_project_data(self, project_id):
    """
    Background optimization of project data
    """
    try:
        project = Project.objects.prefetch_related(
            'tasks', 'team__members', 'sprints'
        ).get(id=project_id)
        
        # Update project completion percentage
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(status='done').count()
        
        if total_tasks > 0:
            completion_percentage = (completed_tasks / total_tasks) * 100
            # You might want to store this in a metrics table
            logger.info(f"Project {project.name} completion: {completion_percentage:.1f}%")
        
        # Invalidate cache
        CacheManager.invalidate_project_cache(project_id)
        
        return f"Optimized data for project {project.name}"
        
    except Project.DoesNotExist:
        logger.error(f"Project {project_id} not found for optimization")
        return f"Project {project_id} not found"
        
    except Exception as e:
        logger.error(f"Error optimizing project {project_id}: {str(e)}")
        self.retry(countdown=120, exc=e)