from rest_framework import serializers
from .models import (
    ProjectMetrics, SprintMetrics, TaskMetrics, TeamMemberMetrics,
    AnalyticsSnapshot, BurndownData, ReportGeneration
)
from projects.models import Project
from tasks.models import Task
from projects.models import TeamMember


class ProjectMetricsSerializer(serializers.ModelSerializer):
    """Serializer for project metrics data"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_status = serializers.CharField(source='project.status', read_only=True)
    
    class Meta:
        model = ProjectMetrics
        fields = [
            'id', 'project', 'project_name', 'project_status',
            'total_tasks', 'completed_tasks', 'in_progress_tasks',
            'todo_tasks', 'blocked_tasks', 'completion_percentage',
            'average_task_completion_time', 'estimated_completion_date',
            'current_velocity', 'average_velocity', 'overdue_tasks',
            'tasks_completed_on_time', 'on_time_completion_rate',
            'active_team_members', 'last_calculated', 'created_at'
        ]
        read_only_fields = ['last_calculated', 'created_at']


class SprintMetricsSerializer(serializers.ModelSerializer):
    """Serializer for sprint metrics"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = SprintMetrics
        fields = [
            'id', 'project', 'project_name', 'sprint_name', 'sprint_number',
            'start_date', 'end_date', 'planned_tasks', 'planned_story_points',
            'completed_tasks', 'completed_story_points', 'velocity',
            'burndown_data', 'sprint_goal_achieved', 'retrospective_notes',
            'days_remaining', 'completion_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_days_remaining(self, obj):
        """Calculate days remaining in sprint"""
        from django.utils import timezone
        if obj.end_date > timezone.now():
            return (obj.end_date.date() - timezone.now().date()).days
        return 0
    
    def get_completion_rate(self, obj):
        """Calculate sprint completion rate"""
        if obj.planned_tasks > 0:
            return (obj.completed_tasks / obj.planned_tasks) * 100
        return 0.0


class TaskMetricsSerializer(serializers.ModelSerializer):
    """Serializer for task metrics"""
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_status = serializers.CharField(source='task.status', read_only=True)
    task_priority = serializers.CharField(source='task.priority', read_only=True)
    assignee_email = serializers.CharField(source='task.assignee.email', read_only=True)
    
    class Meta:
        model = TaskMetrics
        fields = [
            'id', 'task', 'task_title', 'task_status', 'task_priority',
            'assignee_email', 'estimated_hours', 'actual_hours',
            'time_to_completion', 'status_changes', 'assignment_changes',
            'story_points', 'complexity_score', 'reopened_count',
            'blocked_time', 'is_overdue', 'completed_on_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TeamMemberMetricsSerializer(serializers.ModelSerializer):
    """Serializer for team member performance metrics"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.first_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    productivity_score = serializers.SerializerMethodField()
    
    class Meta:
        model = TeamMemberMetrics
        fields = [
            'id', 'user', 'user_email', 'user_name', 'project',
            'project_name', 'tasks_assigned', 'tasks_completed',
            'tasks_in_progress', 'average_completion_time',
            'completion_rate', 'tasks_completed_on_time',
            'on_time_rate', 'story_points_completed',
            'average_velocity', 'comments_made', 'tasks_reviewed',
            'total_time_logged', 'last_activity', 'active_days_count',
            'period_start', 'period_end', 'productivity_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_productivity_score(self, obj):
        """Calculate productivity score based on completion rate and velocity"""
        if obj.completion_rate > 0 and obj.average_velocity > 0:
            return min(100, (obj.completion_rate * 0.6) + (obj.on_time_rate * 0.4))
        return 0.0


class BurndownDataSerializer(serializers.ModelSerializer):
    """Serializer for burndown chart data points"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    sprint_name = serializers.CharField(source='sprint_metrics.sprint_name', read_only=True)
    
    class Meta:
        model = BurndownData
        fields = [
            'id', 'project', 'project_name', 'sprint_metrics', 'sprint_name',
            'date', 'remaining_tasks', 'remaining_story_points',
            'ideal_remaining_tasks', 'ideal_remaining_points',
            'tasks_completed_today', 'story_points_completed_today',
            'team_capacity', 'team_utilization', 'created_at'
        ]
        read_only_fields = ['created_at']


class AnalyticsSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for analytics snapshots"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = AnalyticsSnapshot
        fields = [
            'id', 'project', 'project_name', 'snapshot_type',
            'snapshot_date', 'metrics_data', 'total_tasks',
            'completed_tasks', 'completion_percentage', 'velocity',
            'team_size', 'created_at'
        ]
        read_only_fields = ['created_at']


class ReportGenerationSerializer(serializers.ModelSerializer):
    """Serializer for report generation requests"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportGeneration
        fields = [
            'id', 'project', 'project_name', 'user', 'user_email',
            'report_type', 'export_format', 'date_from', 'date_to',
            'filters', 'status', 'file_path', 'file_size',
            'file_size_mb', 'generation_time', 'error_message',
            'created_at', 'completed_at', 'expires_at'
        ]
        read_only_fields = ['created_at', 'completed_at']
    
    def get_file_size_mb(self, obj):
        """Convert file size to MB"""
        if obj.file_size > 0:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0.0


class ProjectAnalyticsDashboardSerializer(serializers.Serializer):
    """Comprehensive project analytics dashboard data"""
    project = serializers.CharField()
    project_id = serializers.IntegerField()
    metrics = ProjectMetricsSerializer()
    burndown_data = BurndownDataSerializer(many=True)
    velocity_trend = serializers.DictField()
    team_performance = TeamMemberMetricsSerializer(many=True)
    task_breakdown = serializers.ListField()
    priority_breakdown = serializers.ListField()
    recent_activity = serializers.ListField()


class VelocityTrendSerializer(serializers.Serializer):
    """Serializer for velocity trend data"""
    week_start = serializers.DateField()
    week_end = serializers.DateField()
    tasks_completed = serializers.IntegerField()
    story_points_completed = serializers.FloatField()


class ComprehensiveVelocitySerializer(serializers.Serializer):
    """Serializer for comprehensive velocity data"""
    velocity_data = VelocityTrendSerializer(many=True)
    average_tasks_per_week = serializers.FloatField()
    average_points_per_week = serializers.FloatField()
    total_weeks = serializers.IntegerField()


class TeamProductivitySerializer(serializers.Serializer):
    """Serializer for team productivity overview"""
    team_member = serializers.CharField()
    user_id = serializers.IntegerField()
    tasks_assigned = serializers.IntegerField()
    tasks_completed = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    on_time_rate = serializers.FloatField()
    productivity_score = serializers.FloatField()
    last_activity = serializers.DateTimeField()


class ProjectComparisonSerializer(serializers.Serializer):
    """Serializer for comparing multiple projects"""
    project_name = serializers.CharField()
    project_id = serializers.IntegerField()
    completion_percentage = serializers.FloatField()
    current_velocity = serializers.FloatField()
    on_time_rate = serializers.FloatField()
    team_size = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()