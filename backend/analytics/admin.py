from django.contrib import admin
from .models import (
    ProjectMetrics, SprintMetrics, TaskMetrics, TeamMemberMetrics,
    AnalyticsSnapshot, BurndownData, ReportGeneration
)


@admin.register(ProjectMetrics)
class ProjectMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'project', 'total_tasks', 'completed_tasks', 'completion_percentage',
        'current_velocity', 'on_time_completion_rate', 'last_calculated'
    ]
    list_filter = ['last_calculated', 'project__status']
    search_fields = ['project__name']
    readonly_fields = ['last_calculated', 'created_at']
    
    fieldsets = (
        ('Project Info', {
            'fields': ('project',)
        }),
        ('Task Metrics', {
            'fields': (
                'total_tasks', 'completed_tasks', 'in_progress_tasks',
                'todo_tasks', 'blocked_tasks', 'completion_percentage'
            )
        }),
        ('Time Metrics', {
            'fields': (
                'average_task_completion_time', 'estimated_completion_date'
            )
        }),
        ('Velocity Metrics', {
            'fields': ('current_velocity', 'average_velocity')
        }),
        ('Quality Metrics', {
            'fields': (
                'overdue_tasks', 'tasks_completed_on_time', 'on_time_completion_rate'
            )
        }),
        ('Team Metrics', {
            'fields': ('active_team_members',)
        }),
        ('Timestamps', {
            'fields': ('last_calculated', 'created_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SprintMetrics)
class SprintMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'project', 'sprint_name', 'sprint_number', 'start_date',
        'end_date', 'velocity', 'sprint_goal_achieved'
    ]
    list_filter = ['start_date', 'end_date', 'sprint_goal_achieved', 'project']
    search_fields = ['sprint_name', 'project__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Sprint Info', {
            'fields': ('project', 'sprint_name', 'sprint_number', 'start_date', 'end_date')
        }),
        ('Planning', {
            'fields': ('planned_tasks', 'planned_story_points')
        }),
        ('Completion', {
            'fields': ('completed_tasks', 'completed_story_points', 'velocity')
        }),
        ('Burndown Data', {
            'fields': ('burndown_data',),
            'classes': ('collapse',)
        }),
        ('Retrospective', {
            'fields': ('sprint_goal_achieved', 'retrospective_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(TaskMetrics)
class TaskMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'task', 'estimated_hours', 'actual_hours', 'time_to_completion',
        'story_points', 'is_overdue', 'completed_on_time'
    ]
    list_filter = [
        'is_overdue', 'completed_on_time', 'complexity_score',
        'task__status', 'task__priority'
    ]
    search_fields = ['task__title', 'task__project__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Task Info', {
            'fields': ('task',)
        }),
        ('Time Tracking', {
            'fields': ('estimated_hours', 'actual_hours', 'time_to_completion')
        }),
        ('Complexity', {
            'fields': ('story_points', 'complexity_score')
        }),
        ('Quality Metrics', {
            'fields': ('reopened_count', 'blocked_time', 'is_overdue', 'completed_on_time')
        }),
        ('Change Tracking', {
            'fields': ('status_changes', 'assignment_changes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(TeamMemberMetrics)
class TeamMemberMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'project', 'tasks_assigned', 'tasks_completed',
        'completion_rate', 'on_time_rate', 'period_start', 'period_end'
    ]
    list_filter = ['period_start', 'period_end', 'project']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'project__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Member Info', {
            'fields': ('user', 'project', 'period_start', 'period_end')
        }),
        ('Task Metrics', {
            'fields': ('tasks_assigned', 'tasks_completed', 'tasks_in_progress')
        }),
        ('Performance', {
            'fields': ('average_completion_time', 'completion_rate')
        }),
        ('Quality', {
            'fields': ('tasks_completed_on_time', 'on_time_rate')
        }),
        ('Velocity', {
            'fields': ('story_points_completed', 'average_velocity')
        }),
        ('Collaboration', {
            'fields': ('comments_made', 'tasks_reviewed')
        }),
        ('Activity', {
            'fields': ('total_time_logged', 'last_activity', 'active_days_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'project', 'snapshot_type', 'snapshot_date',
        'total_tasks', 'completed_tasks', 'completion_percentage',
        'velocity', 'team_size'
    ]
    list_filter = ['snapshot_type', 'snapshot_date', 'project']
    search_fields = ['project__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Snapshot Info', {
            'fields': ('project', 'snapshot_type', 'snapshot_date')
        }),
        ('Key Metrics', {
            'fields': (
                'total_tasks', 'completed_tasks', 'completion_percentage',
                'velocity', 'team_size'
            )
        }),
        ('Detailed Data', {
            'fields': ('metrics_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(BurndownData)
class BurndownDataAdmin(admin.ModelAdmin):
    list_display = [
        'project', 'date', 'remaining_tasks', 'ideal_remaining_tasks',
        'tasks_completed_today', 'team_utilization'
    ]
    list_filter = ['date', 'project']
    search_fields = ['project__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('project', 'sprint_metrics', 'date')
        }),
        ('Remaining Work', {
            'fields': ('remaining_tasks', 'remaining_story_points')
        }),
        ('Ideal Burndown', {
            'fields': ('ideal_remaining_tasks', 'ideal_remaining_points')
        }),
        ('Daily Progress', {
            'fields': ('tasks_completed_today', 'story_points_completed_today')
        }),
        ('Team Capacity', {
            'fields': ('team_capacity', 'team_utilization')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(ReportGeneration)
class ReportGenerationAdmin(admin.ModelAdmin):
    list_display = [
        'project', 'user', 'report_type', 'export_format',
        'status', 'created_at', 'completed_at'
    ]
    list_filter = ['report_type', 'export_format', 'status', 'created_at']
    search_fields = ['project__name', 'user__email']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = (
        ('Report Info', {
            'fields': ('project', 'user', 'report_type', 'export_format')
        }),
        ('Parameters', {
            'fields': ('date_from', 'date_to', 'filters')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('File Info', {
            'fields': ('file_path', 'file_size', 'generation_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at', 'expires_at'),
            'classes': ('collapse',)
        })
    )
