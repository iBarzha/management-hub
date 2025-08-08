from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from projects.models import Project
from tasks.models import Task
from projects.models import TeamMember

User = get_user_model()


class ProjectMetrics(models.Model):
    """Store calculated project metrics for performance"""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='metrics')
    
    # Task metrics
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    in_progress_tasks = models.IntegerField(default=0)
    todo_tasks = models.IntegerField(default=0)
    blocked_tasks = models.IntegerField(default=0)
    
    # Progress metrics
    completion_percentage = models.FloatField(default=0.0)
    
    # Time metrics
    average_task_completion_time = models.FloatField(default=0.0)  # in hours
    estimated_completion_date = models.DateTimeField(null=True, blank=True)
    
    # Velocity metrics
    current_velocity = models.FloatField(default=0.0)  # tasks per week
    average_velocity = models.FloatField(default=0.0)
    
    # Quality metrics
    overdue_tasks = models.IntegerField(default=0)
    tasks_completed_on_time = models.IntegerField(default=0)
    on_time_completion_rate = models.FloatField(default=0.0)
    
    # Team metrics
    active_team_members = models.IntegerField(default=0)
    
    # Timestamps
    last_calculated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_metrics'
        ordering = ['-last_calculated']
        
    def __str__(self):
        return f"Metrics for {self.project.name}"


class SprintMetrics(models.Model):
    """Track sprint-specific metrics for velocity and burndown charts"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprint_metrics')
    sprint_name = models.CharField(max_length=200)
    sprint_number = models.IntegerField()
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Sprint planning metrics
    planned_tasks = models.IntegerField(default=0)
    planned_story_points = models.FloatField(default=0.0)
    
    # Sprint completion metrics
    completed_tasks = models.IntegerField(default=0)
    completed_story_points = models.FloatField(default=0.0)
    
    # Sprint velocity
    velocity = models.FloatField(default=0.0)  # completed story points
    
    # Sprint burndown data (JSON field for daily progress)
    burndown_data = models.JSONField(default=list)
    
    # Sprint retrospective data
    sprint_goal_achieved = models.BooleanField(default=False)
    retrospective_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sprint_metrics'
        unique_together = ['project', 'sprint_number']
        ordering = ['-sprint_number']
        
    def __str__(self):
        return f"{self.project.name} - Sprint {self.sprint_number}"


class TaskMetrics(models.Model):
    """Individual task performance metrics"""
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='metrics')
    
    # Time tracking
    estimated_hours = models.FloatField(default=0.0)
    actual_hours = models.FloatField(default=0.0)
    time_to_completion = models.FloatField(default=0.0)  # hours from creation to completion
    
    # Status change tracking
    status_changes = models.JSONField(default=list)  # [{status: 'todo', timestamp: '...', user: '...'}, ...]
    
    # Assignment tracking
    assignment_changes = models.JSONField(default=list)  # Track reassignments
    
    # Complexity metrics
    story_points = models.FloatField(default=0.0)
    complexity_score = models.IntegerField(default=1, choices=[(1, 'Very Low'), (2, 'Low'), (3, 'Medium'), (4, 'High'), (5, 'Very High')])
    
    # Quality metrics
    reopened_count = models.IntegerField(default=0)
    blocked_time = models.FloatField(default=0.0)  # total hours in blocked state
    
    # Performance flags
    is_overdue = models.BooleanField(default=False)
    completed_on_time = models.BooleanField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_metrics'
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"Metrics for {self.task.title}"


class TeamMemberMetrics(models.Model):
    """Individual team member performance metrics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_metrics')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='member_metrics')
    
    # Task completion metrics
    tasks_assigned = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    tasks_in_progress = models.IntegerField(default=0)
    
    # Performance metrics
    average_completion_time = models.FloatField(default=0.0)  # hours
    completion_rate = models.FloatField(default=0.0)  # percentage
    
    # Quality metrics
    tasks_completed_on_time = models.IntegerField(default=0)
    on_time_rate = models.FloatField(default=0.0)
    
    # Velocity metrics
    story_points_completed = models.FloatField(default=0.0)
    average_velocity = models.FloatField(default=0.0)  # story points per week
    
    # Collaboration metrics
    comments_made = models.IntegerField(default=0)
    tasks_reviewed = models.IntegerField(default=0)
    
    # Time tracking
    total_time_logged = models.FloatField(default=0.0)  # hours
    
    # Engagement metrics
    last_activity = models.DateTimeField(null=True, blank=True)
    active_days_count = models.IntegerField(default=0)
    
    # Performance period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'team_member_metrics'
        unique_together = ['user', 'project', 'period_start']
        ordering = ['-period_start']
        
    def __str__(self):
        return f"{self.user.email} metrics for {self.project.name}"


class AnalyticsSnapshot(models.Model):
    """Daily/weekly snapshots for historical trending"""
    SNAPSHOT_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='analytics_snapshots')
    snapshot_type = models.CharField(max_length=10, choices=SNAPSHOT_TYPES)
    snapshot_date = models.DateTimeField()
    
    # Snapshot data (JSON)
    metrics_data = models.JSONField(default=dict)
    
    # Key metrics for easy querying
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    completion_percentage = models.FloatField(default=0.0)
    velocity = models.FloatField(default=0.0)
    team_size = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_snapshots'
        unique_together = ['project', 'snapshot_type', 'snapshot_date']
        ordering = ['-snapshot_date']
        
    def __str__(self):
        return f"{self.project.name} {self.snapshot_type} snapshot - {self.snapshot_date.date()}"


class BurndownData(models.Model):
    """Daily burndown chart data points"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='burndown_data')
    sprint_metrics = models.ForeignKey(SprintMetrics, on_delete=models.CASCADE, related_name='daily_burndown', null=True, blank=True)
    
    date = models.DateField()
    
    # Remaining work
    remaining_tasks = models.IntegerField(default=0)
    remaining_story_points = models.FloatField(default=0.0)
    
    # Ideal burndown
    ideal_remaining_tasks = models.FloatField(default=0.0)
    ideal_remaining_points = models.FloatField(default=0.0)
    
    # Completed work
    tasks_completed_today = models.IntegerField(default=0)
    story_points_completed_today = models.FloatField(default=0.0)
    
    # Team capacity
    team_capacity = models.FloatField(default=0.0)  # available hours
    team_utilization = models.FloatField(default=0.0)  # percentage
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'burndown_data'
        unique_together = ['project', 'date']
        ordering = ['date']
        
    def __str__(self):
        return f"{self.project.name} burndown - {self.date}"


class ReportGeneration(models.Model):
    """Track generated reports for caching and management"""
    REPORT_TYPES = [
        ('project_summary', 'Project Summary'),
        ('team_performance', 'Team Performance'),
        ('sprint_report', 'Sprint Report'),
        ('velocity_report', 'Velocity Report'),
        ('burndown_report', 'Burndown Report'),
        ('custom', 'Custom Report'),
    ]
    
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='generated_reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_reports')
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    
    # Report parameters
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    filters = models.JSONField(default=dict)
    
    # Generation status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(default=0)
    
    # Metadata
    generation_time = models.FloatField(default=0.0)  # seconds
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'report_generations'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.report_type} report for {self.project.name} ({self.status})"
