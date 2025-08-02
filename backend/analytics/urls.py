from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'analytics'

urlpatterns = [
    # Project Metrics
    path('projects/metrics/', views.ProjectMetricsListView.as_view(), name='project-metrics-list'),
    path('projects/<int:project_id>/metrics/', views.ProjectMetricsDetailView.as_view(), name='project-metrics-detail'),
    path('projects/<int:project_id>/dashboard/', views.ProjectAnalyticsDashboardView.as_view(), name='project-dashboard'),
    path('projects/<int:project_id>/metrics/refresh/', views.refresh_project_metrics, name='refresh-project-metrics'),
    
    # Burndown Charts
    path('projects/<int:project_id>/burndown/', views.BurndownChartDataView.as_view(), name='burndown-data'),
    
    # Velocity Tracking
    path('projects/<int:project_id>/velocity/', views.VelocityTrendView.as_view(), name='velocity-trend'),
    
    # Team Performance
    path('projects/<int:project_id>/team-performance/', views.TeamPerformanceView.as_view(), name='team-performance'),
    
    # Task Metrics
    path('tasks/metrics/', views.TaskMetricsListView.as_view(), name='task-metrics-list'),
    
    # Sprint Metrics
    path('sprints/metrics/', views.SprintMetricsListView.as_view(), name='sprint-metrics-list'),
    
    # Project Comparison
    path('projects/comparison/', views.ProjectComparisonView.as_view(), name='project-comparison'),
    
    # Reports
    path('reports/generate/', views.GenerateReportView.as_view(), name='generate-report'),
    
    # Analytics Snapshots
    path('snapshots/', views.AnalyticsSnapshotListView.as_view(), name='analytics-snapshots'),
    path('projects/<int:project_id>/snapshots/', views.create_analytics_snapshot, name='create-snapshot'),
]