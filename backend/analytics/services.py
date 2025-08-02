import csv
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from django.db.models import Count, Avg, Q, F, Sum
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import (
    ProjectMetrics, SprintMetrics, TaskMetrics, TeamMemberMetrics,
    AnalyticsSnapshot, BurndownData, ReportGeneration
)
from projects.models import Project
from tasks.models import Task
from projects.models import TeamMember

User = get_user_model()


class MetricsCalculationService:
    """Service for calculating and updating project metrics"""
    
    @staticmethod
    def calculate_project_metrics(project: Project) -> ProjectMetrics:
        """Calculate comprehensive project metrics"""
        with transaction.atomic():
            # Get or create project metrics
            metrics, created = ProjectMetrics.objects.get_or_create(project=project)
            
            # Task status counts
            task_counts = Task.objects.filter(project=project).aggregate(
                total=Count('id'),
                completed=Count('id', filter=Q(status='done')),
                in_progress=Count('id', filter=Q(status='in_progress')),
                todo=Count('id', filter=Q(status='todo')),
                blocked=Count('id', filter=Q(status='blocked'))
            )
            
            metrics.total_tasks = task_counts['total'] or 0
            metrics.completed_tasks = task_counts['completed'] or 0
            metrics.in_progress_tasks = task_counts['in_progress'] or 0
            metrics.todo_tasks = task_counts['todo'] or 0
            metrics.blocked_tasks = task_counts['blocked'] or 0
            
            # Calculate completion percentage
            if metrics.total_tasks > 0:
                metrics.completion_percentage = (metrics.completed_tasks / metrics.total_tasks) * 100
            else:
                metrics.completion_percentage = 0.0
            
            # Calculate overdue tasks
            now = timezone.now()
            metrics.overdue_tasks = Task.objects.filter(
                project=project,
                due_date__lt=now,
                status__in=['todo', 'in_progress', 'blocked']
            ).count()
            
            # Calculate on-time completion rate
            completed_tasks = Task.objects.filter(project=project, status='done')
            on_time_count = 0
            total_completed = completed_tasks.count()
            
            for task in completed_tasks:
                if task.due_date and task.updated_at <= task.due_date:
                    on_time_count += 1
            
            metrics.tasks_completed_on_time = on_time_count
            if total_completed > 0:
                metrics.on_time_completion_rate = (on_time_count / total_completed) * 100
            else:
                metrics.on_time_completion_rate = 0.0
            
            # Calculate average task completion time
            completed_tasks_with_metrics = TaskMetrics.objects.filter(
                task__project=project,
                task__status='done',
                time_to_completion__gt=0
            )
            
            if completed_tasks_with_metrics.exists():
                avg_time = completed_tasks_with_metrics.aggregate(
                    avg=Avg('time_to_completion')
                )['avg']
                metrics.average_task_completion_time = avg_time or 0.0
            else:
                metrics.average_task_completion_time = 0.0
            
            # Calculate velocity (tasks completed per week in last 4 weeks)
            four_weeks_ago = now - timedelta(weeks=4)
            recent_completed = Task.objects.filter(
                project=project,
                status='done',
                updated_at__gte=four_weeks_ago
            ).count()
            metrics.current_velocity = recent_completed / 4  # per week
            
            # Calculate team metrics
            metrics.active_team_members = TeamMember.objects.filter(
                team=project.team,
                is_active=True
            ).count()
            
            # Estimate completion date based on current velocity
            if metrics.current_velocity > 0 and metrics.total_tasks > metrics.completed_tasks:
                remaining_tasks = metrics.total_tasks - metrics.completed_tasks
                weeks_remaining = remaining_tasks / metrics.current_velocity
                metrics.estimated_completion_date = now + timedelta(weeks=weeks_remaining)
            
            metrics.save()
            return metrics
    
    @staticmethod
    def calculate_task_metrics(task: Task) -> TaskMetrics:
        """Calculate individual task metrics"""
        with transaction.atomic():
            metrics, created = TaskMetrics.objects.get_or_create(task=task)
            
            # Calculate time to completion if task is done
            if task.status == 'done' and not metrics.time_to_completion:
                time_diff = task.updated_at - task.created_at
                metrics.time_to_completion = time_diff.total_seconds() / 3600  # hours
            
            # Check if task is overdue
            if task.due_date:
                metrics.is_overdue = timezone.now() > task.due_date and task.status != 'done'
                
                # Check if completed on time
                if task.status == 'done':
                    metrics.completed_on_time = task.updated_at <= task.due_date
            
            # Track status changes (this would be called from task update signals)
            # For now, we'll just save what we have
            metrics.save()
            return metrics
    
    @staticmethod
    def calculate_team_member_metrics(user: User, project: Project, 
                                    period_start: datetime, period_end: datetime) -> TeamMemberMetrics:
        """Calculate team member performance metrics for a specific period"""
        with transaction.atomic():
            metrics, created = TeamMemberMetrics.objects.get_or_create(
                user=user,
                project=project,
                period_start=period_start,
                defaults={'period_end': period_end}
            )
            
            # Task assignment metrics
            user_tasks = Task.objects.filter(
                project=project,
                assignee=user,
                created_at__range=[period_start, period_end]
            )
            
            metrics.tasks_assigned = user_tasks.count()
            metrics.tasks_completed = user_tasks.filter(status='done').count()
            metrics.tasks_in_progress = user_tasks.filter(status='in_progress').count()
            
            # Calculate completion rate
            if metrics.tasks_assigned > 0:
                metrics.completion_rate = (metrics.tasks_completed / metrics.tasks_assigned) * 100
            else:
                metrics.completion_rate = 0.0
            
            # Calculate average completion time
            completed_task_metrics = TaskMetrics.objects.filter(
                task__project=project,
                task__assignee=user,
                task__status='done',
                task__updated_at__range=[period_start, period_end],
                time_to_completion__gt=0
            )
            
            if completed_task_metrics.exists():
                avg_time = completed_task_metrics.aggregate(avg=Avg('time_to_completion'))['avg']
                metrics.average_completion_time = avg_time or 0.0
            
            # Calculate on-time completion metrics
            completed_tasks = user_tasks.filter(status='done')
            on_time_count = 0
            
            for task in completed_tasks:
                if task.due_date and task.updated_at <= task.due_date:
                    on_time_count += 1
            
            metrics.tasks_completed_on_time = on_time_count
            if metrics.tasks_completed > 0:
                metrics.on_time_rate = (on_time_count / metrics.tasks_completed) * 100
            else:
                metrics.on_time_rate = 0.0
            
            # Update last activity
            latest_task_activity = user_tasks.order_by('-updated_at').first()
            if latest_task_activity:
                metrics.last_activity = latest_task_activity.updated_at
            
            metrics.save()
            return metrics


class BurndownService:
    """Service for generating burndown chart data"""
    
    @staticmethod
    def generate_burndown_data(project: Project, start_date: date = None, 
                             end_date: date = None) -> List[Dict[str, Any]]:
        """Generate burndown chart data for a project"""
        if not start_date:
            start_date = project.created_at.date()
        if not end_date:
            end_date = timezone.now().date()
        
        burndown_data = []
        current_date = start_date
        
        # Get initial task count
        initial_tasks = Task.objects.filter(
            project=project,
            created_at__date__lte=start_date
        ).count()
        
        while current_date <= end_date:
            # Calculate remaining tasks at end of day
            remaining_tasks = Task.objects.filter(
                project=project,
                created_at__date__lte=current_date
            ).exclude(
                status='done',
                updated_at__date__lte=current_date
            ).count()
            
            # Calculate completed tasks on this day
            tasks_completed_today = Task.objects.filter(
                project=project,
                status='done',
                updated_at__date=current_date
            ).count()
            
            # Calculate ideal burndown (linear)
            total_days = (end_date - start_date).days + 1
            days_passed = (current_date - start_date).days + 1
            ideal_remaining = max(0, initial_tasks - (initial_tasks * days_passed / total_days))
            
            burndown_point = {
                'date': current_date.isoformat(),
                'remaining_tasks': remaining_tasks,
                'ideal_remaining_tasks': ideal_remaining,
                'tasks_completed_today': tasks_completed_today
            }
            
            burndown_data.append(burndown_point)
            
            # Store in database for caching
            BurndownData.objects.update_or_create(
                project=project,
                date=current_date,
                defaults={
                    'remaining_tasks': remaining_tasks,
                    'ideal_remaining_tasks': ideal_remaining,
                    'tasks_completed_today': tasks_completed_today
                }
            )
            
            current_date += timedelta(days=1)
        
        return burndown_data
    
    @staticmethod
    def get_cached_burndown_data(project: Project, days: int = 30) -> List[Dict[str, Any]]:
        """Get cached burndown data from database"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        cached_data = BurndownData.objects.filter(
            project=project,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        return [
            {
                'date': data.date.isoformat(),
                'remaining_tasks': data.remaining_tasks,
                'ideal_remaining_tasks': data.ideal_remaining_tasks,
                'tasks_completed_today': data.tasks_completed_today,
                'team_capacity': data.team_capacity,
                'team_utilization': data.team_utilization
            }
            for data in cached_data
        ]


class VelocityService:
    """Service for tracking team velocity"""
    
    @staticmethod
    def calculate_velocity_trend(project: Project, weeks: int = 12) -> Dict[str, Any]:
        """Calculate velocity trend over specified weeks"""
        end_date = timezone.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        velocity_data = []
        current_start = start_date
        
        while current_start < end_date:
            week_end = current_start + timedelta(days=7)
            
            # Count tasks completed in this week
            tasks_completed = Task.objects.filter(
                project=project,
                status='done',
                updated_at__range=[current_start, week_end]
            ).count()
            
            # Calculate story points if available
            story_points = TaskMetrics.objects.filter(
                task__project=project,
                task__status='done',
                task__updated_at__range=[current_start, week_end]
            ).aggregate(total=Sum('story_points'))['total'] or 0
            
            velocity_data.append({
                'week_start': current_start.date().isoformat(),
                'week_end': week_end.date().isoformat(),
                'tasks_completed': tasks_completed,
                'story_points_completed': float(story_points)
            })
            
            current_start = week_end
        
        # Calculate averages
        total_tasks = sum(week['tasks_completed'] for week in velocity_data)
        total_points = sum(week['story_points_completed'] for week in velocity_data)
        
        return {
            'velocity_data': velocity_data,
            'average_tasks_per_week': total_tasks / len(velocity_data) if velocity_data else 0,
            'average_points_per_week': total_points / len(velocity_data) if velocity_data else 0,
            'total_weeks': len(velocity_data)
        }


class ReportService:
    """Service for generating various reports"""
    
    @staticmethod
    def generate_project_summary_data(project: Project, 
                                    date_from: datetime, 
                                    date_to: datetime) -> Dict[str, Any]:
        """Generate project summary report data"""
        metrics = MetricsCalculationService.calculate_project_metrics(project)
        
        # Task breakdown
        task_breakdown = Task.objects.filter(
            project=project,
            created_at__range=[date_from, date_to]
        ).values('status').annotate(count=Count('id'))
        
        # Priority breakdown
        priority_breakdown = Task.objects.filter(
            project=project,
            created_at__range=[date_from, date_to]
        ).values('priority').annotate(count=Count('id'))
        
        # Team performance
        team_members = TeamMember.objects.filter(team=project.team, is_active=True)
        team_performance = []
        
        for member in team_members:
            member_metrics = MetricsCalculationService.calculate_team_member_metrics(
                member.user, project, date_from, date_to
            )
            team_performance.append({
                'user': member.user.email,
                'tasks_assigned': member_metrics.tasks_assigned,
                'tasks_completed': member_metrics.tasks_completed,
                'completion_rate': member_metrics.completion_rate,
                'on_time_rate': member_metrics.on_time_rate
            })
        
        return {
            'project': {
                'name': project.name,
                'description': project.description,
                'status': project.status,
                'created_at': project.created_at.isoformat(),
            },
            'metrics': {
                'total_tasks': metrics.total_tasks,
                'completed_tasks': metrics.completed_tasks,
                'completion_percentage': metrics.completion_percentage,
                'current_velocity': metrics.current_velocity,
                'on_time_completion_rate': metrics.on_time_completion_rate,
                'overdue_tasks': metrics.overdue_tasks,
                'active_team_members': metrics.active_team_members
            },
            'task_breakdown': list(task_breakdown),
            'priority_breakdown': list(priority_breakdown),
            'team_performance': team_performance,
            'burndown_data': BurndownService.get_cached_burndown_data(project, 30),
            'velocity_trend': VelocityService.calculate_velocity_trend(project, 8)
        }
    
    @staticmethod
    def export_to_csv(data: Dict[str, Any], report_type: str) -> str:
        """Export report data to CSV format"""
        import io
        
        output = io.StringIO()
        
        if report_type == 'project_summary':
            writer = csv.writer(output)
            
            # Project info
            writer.writerow(['Project Summary Report'])
            writer.writerow(['Project Name', data['project']['name']])
            writer.writerow(['Status', data['project']['status']])
            writer.writerow([''])
            
            # Metrics
            writer.writerow(['Metrics'])
            writer.writerow(['Total Tasks', data['metrics']['total_tasks']])
            writer.writerow(['Completed Tasks', data['metrics']['completed_tasks']])
            writer.writerow(['Completion %', f"{data['metrics']['completion_percentage']:.1f}%"])
            writer.writerow(['Current Velocity', f"{data['metrics']['current_velocity']:.1f} tasks/week"])
            writer.writerow(['On-time Rate', f"{data['metrics']['on_time_completion_rate']:.1f}%"])
            writer.writerow([''])
            
            # Task breakdown
            writer.writerow(['Task Status Breakdown'])
            writer.writerow(['Status', 'Count'])
            for item in data['task_breakdown']:
                writer.writerow([item['status'], item['count']])
            writer.writerow([''])
            
            # Team performance
            writer.writerow(['Team Performance'])
            writer.writerow(['Team Member', 'Assigned', 'Completed', 'Completion Rate', 'On-time Rate'])
            for member in data['team_performance']:
                writer.writerow([
                    member['user'],
                    member['tasks_assigned'],
                    member['tasks_completed'],
                    f"{member['completion_rate']:.1f}%",
                    f"{member['on_time_rate']:.1f}%"
                ])
        
        return output.getvalue()


class AnalyticsCacheService:
    """Service for caching analytics data"""
    
    @staticmethod
    def get_cached_metrics(project: Project) -> Optional[Dict[str, Any]]:
        """Get cached project metrics"""
        cache_key = f"project_metrics_{project.id}"
        return cache.get(cache_key)
    
    @staticmethod
    def cache_metrics(project: Project, metrics_data: Dict[str, Any], timeout: int = 3600):
        """Cache project metrics for specified timeout (default 1 hour)"""
        cache_key = f"project_metrics_{project.id}"
        cache.set(cache_key, metrics_data, timeout)
    
    @staticmethod
    def invalidate_project_cache(project: Project):
        """Invalidate all cached data for a project"""
        cache_keys = [
            f"project_metrics_{project.id}",
            f"burndown_data_{project.id}",
            f"velocity_data_{project.id}",
            f"team_performance_{project.id}"
        ]
        cache.delete_many(cache_keys)
    
    @staticmethod
    def create_analytics_snapshot(project: Project, snapshot_type: str = 'daily'):
        """Create a snapshot of current analytics data"""
        metrics = MetricsCalculationService.calculate_project_metrics(project)
        
        snapshot_data = {
            'total_tasks': metrics.total_tasks,
            'completed_tasks': metrics.completed_tasks,
            'completion_percentage': metrics.completion_percentage,
            'current_velocity': metrics.current_velocity,
            'on_time_completion_rate': metrics.on_time_completion_rate,
            'overdue_tasks': metrics.overdue_tasks,
            'active_team_members': metrics.active_team_members,
            'timestamp': timezone.now().isoformat()
        }
        
        AnalyticsSnapshot.objects.create(
            project=project,
            snapshot_type=snapshot_type,
            snapshot_date=timezone.now(),
            metrics_data=snapshot_data,
            total_tasks=metrics.total_tasks,
            completed_tasks=metrics.completed_tasks,
            completion_percentage=metrics.completion_percentage,
            velocity=metrics.current_velocity,
            team_size=metrics.active_team_members
        )