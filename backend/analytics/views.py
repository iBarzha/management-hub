from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    ProjectMetrics, SprintMetrics, TaskMetrics, TeamMemberMetrics,
    AnalyticsSnapshot, BurndownData, ReportGeneration
)
from .serializers import (
    ProjectMetricsSerializer, SprintMetricsSerializer, TaskMetricsSerializer,
    TeamMemberMetricsSerializer, BurndownDataSerializer, AnalyticsSnapshotSerializer,
    ReportGenerationSerializer, ProjectAnalyticsDashboardSerializer,
    ComprehensiveVelocitySerializer, TeamProductivitySerializer,
    ProjectComparisonSerializer
)
from .services import (
    MetricsCalculationService, BurndownService, VelocityService,
    ReportService, AnalyticsCacheService
)
from projects.models import Project
from tasks.models import Task
from projects.models import TeamMember


class ProjectMetricsListView(generics.ListAPIView):
    """List project metrics for all projects user has access to"""
    serializer_class = ProjectMetricsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Get projects where user is a team member
        user_projects = Project.objects.filter(
            team__members__user=user,
            team__members__is_active=True
        ).distinct()
        
        return ProjectMetrics.objects.filter(project__in=user_projects).select_related('project')


class ProjectMetricsDetailView(generics.RetrieveAPIView):
    """Get detailed metrics for a specific project"""
    serializer_class = ProjectMetricsSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'project__id'
    lookup_url_kwarg = 'project_id'
    
    def get_object(self):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id)
        
        # Check if user has access to this project
        if not project.team.members.filter(user=self.request.user, is_active=True).exists():
            self.permission_denied(self.request)
        
        # Calculate fresh metrics
        return MetricsCalculationService.calculate_project_metrics(project)


class ProjectAnalyticsDashboardView(APIView):
    """Comprehensive analytics dashboard for a project"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        
        # Check access
        if not project.team.members.filter(user=request.user, is_active=True).exists():
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Date range parameters
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Check cache first
        cached_data = AnalyticsCacheService.get_cached_metrics(project)
        if cached_data and not request.query_params.get('refresh'):
            return Response(cached_data)
        
        # Generate fresh data
        dashboard_data = ReportService.generate_project_summary_data(
            project, start_date, end_date
        )
        
        # Cache the results
        AnalyticsCacheService.cache_metrics(project, dashboard_data)
        
        return Response(dashboard_data)


class BurndownChartDataView(APIView):
    """Generate burndown chart data for a project"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        
        # Check access
        if not project.team.members.filter(user=request.user, is_active=True).exists():
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get parameters
        days = int(request.query_params.get('days', 30))
        use_cache = request.query_params.get('cache', 'true').lower() == 'true'
        
        if use_cache:
            burndown_data = BurndownService.get_cached_burndown_data(project, days)
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            burndown_data = BurndownService.generate_burndown_data(project, start_date, end_date)
        
        return Response({
            'project_id': project_id,
            'project_name': project.name,
            'burndown_data': burndown_data,
            'days_requested': days
        })


class VelocityTrendView(APIView):
    """Get velocity trend data for a project"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        
        # Check access
        if not project.team.members.filter(user=request.user, is_active=True).exists():
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        weeks = int(request.query_params.get('weeks', 12))
        velocity_data = VelocityService.calculate_velocity_trend(project, weeks)
        
        return Response({
            'project_id': project_id,
            'project_name': project.name,
            'velocity_trend': velocity_data
        })


class TeamPerformanceView(APIView):
    """Get team performance metrics for a project"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        
        # Check access
        if not project.team.members.filter(user=request.user, is_active=True).exists():
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Date range
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get team members
        team_members = project.team.members.filter(is_active=True)
        performance_data = []
        
        for member in team_members:
            metrics = MetricsCalculationService.calculate_team_member_metrics(
                member.user, project, start_date, end_date
            )
            
            performance_data.append({
                'user_id': member.user.id,
                'user_email': member.user.email,
                'user_name': f"{member.user.first_name} {member.user.last_name}".strip(),
                'role': member.role,
                'tasks_assigned': metrics.tasks_assigned,
                'tasks_completed': metrics.tasks_completed,
                'completion_rate': metrics.completion_rate,
                'on_time_rate': metrics.on_time_rate,
                'average_completion_time': metrics.average_completion_time,
                'last_activity': metrics.last_activity,
                'productivity_score': min(100, (metrics.completion_rate * 0.6) + (metrics.on_time_rate * 0.4))
            })
        
        return Response({
            'project_id': project_id,
            'project_name': project.name,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'team_performance': performance_data
        })


class TaskMetricsListView(generics.ListAPIView):
    """List task metrics with filtering"""
    serializer_class = TaskMetricsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        project_id = self.request.query_params.get('project_id')
        assignee_id = self.request.query_params.get('assignee_id')
        overdue_only = self.request.query_params.get('overdue', 'false').lower() == 'true'
        
        queryset = TaskMetrics.objects.select_related('task', 'task__project', 'task__assignee')
        
        # Filter by user's accessible projects
        user_projects = Project.objects.filter(
            team__members__user=user,
            team__members__is_active=True
        ).distinct()
        queryset = queryset.filter(task__project__in=user_projects)
        
        # Additional filters
        if project_id:
            queryset = queryset.filter(task__project_id=project_id)
        
        if assignee_id:
            queryset = queryset.filter(task__assignee_id=assignee_id)
        
        if overdue_only:
            queryset = queryset.filter(is_overdue=True)
        
        return queryset.order_by('-created_at')


class SprintMetricsListView(generics.ListAPIView):
    """List sprint metrics for a project"""
    serializer_class = SprintMetricsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        project_id = self.request.query_params.get('project_id')
        
        queryset = SprintMetrics.objects.select_related('project')
        
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            # Check access
            if not project.team.members.filter(user=user, is_active=True).exists():
                return SprintMetrics.objects.none()
            queryset = queryset.filter(project=project)
        else:
            # Filter by accessible projects
            user_projects = Project.objects.filter(
                team__members__user=user,
                team__members__is_active=True
            ).distinct()
            queryset = queryset.filter(project__in=user_projects)
        
        return queryset.order_by('-sprint_number')


class ProjectComparisonView(APIView):
    """Compare metrics across multiple projects"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get all projects user has access to
        user_projects = Project.objects.filter(
            team__members__user=user,
            team__members__is_active=True
        ).distinct()
        
        comparison_data = []
        
        for project in user_projects:
            metrics = ProjectMetrics.objects.filter(project=project).first()
            if not metrics:
                metrics = MetricsCalculationService.calculate_project_metrics(project)
            
            comparison_data.append({
                'project_id': project.id,
                'project_name': project.name,
                'project_status': project.status,
                'completion_percentage': metrics.completion_percentage,
                'current_velocity': metrics.current_velocity,
                'on_time_rate': metrics.on_time_completion_rate,
                'team_size': metrics.active_team_members,
                'total_tasks': metrics.total_tasks,
                'completed_tasks': metrics.completed_tasks,
                'overdue_tasks': metrics.overdue_tasks,
                'last_updated': metrics.last_calculated.isoformat()
            })
        
        return Response({
            'total_projects': len(comparison_data),
            'projects': comparison_data
        })


class GenerateReportView(APIView):
    """Generate and export reports"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        project_id = request.data.get('project_id')
        report_type = request.data.get('report_type', 'project_summary')
        export_format = request.data.get('export_format', 'csv')
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')
        
        # Validate project access
        project = get_object_or_404(Project, id=project_id)
        if not project.team.members.filter(user=request.user, is_active=True).exists():
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Parse dates
        try:
            date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return Response(
                {'error': 'Invalid date format. Use ISO format.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create report generation record
        report_generation = ReportGeneration.objects.create(
            project=project,
            user=request.user,
            report_type=report_type,
            export_format=export_format,
            date_from=date_from,
            date_to=date_to,
            status='pending'
        )
        
        try:
            # Generate report data
            report_generation.status = 'generating'
            report_generation.save()
            
            report_data = ReportService.generate_project_summary_data(
                project, date_from, date_to
            )
            
            if export_format == 'csv':
                csv_content = ReportService.export_to_csv(report_data, report_type)
                
                response = HttpResponse(csv_content, content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{project.name}_{report_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
                
                report_generation.status = 'completed'
                report_generation.completed_at = timezone.now()
                report_generation.save()
                
                return response
            
            elif export_format == 'json':
                report_generation.status = 'completed'
                report_generation.completed_at = timezone.now()
                report_generation.save()
                
                return Response(report_data)
            
            else:
                report_generation.status = 'failed'
                report_generation.error_message = 'Unsupported export format'
                report_generation.save()
                
                return Response(
                    {'error': 'Unsupported export format'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            report_generation.status = 'failed'
            report_generation.error_message = str(e)
            report_generation.save()
            
            return Response(
                {'error': 'Failed to generate report'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def refresh_project_metrics(request, project_id):
    """Force refresh project metrics and clear cache"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check access
    if not project.team.members.filter(user=request.user, is_active=True).exists():
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Clear cache
    AnalyticsCacheService.invalidate_project_cache(project)
    
    # Recalculate metrics
    metrics = MetricsCalculationService.calculate_project_metrics(project)
    serializer = ProjectMetricsSerializer(metrics)
    
    return Response({
        'message': 'Metrics refreshed successfully',
        'metrics': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_analytics_snapshot(request, project_id):
    """Create an analytics snapshot for historical tracking"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check access
    if not project.team.members.filter(user=request.user, is_active=True).exists():
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    snapshot_type = request.data.get('snapshot_type', 'manual')
    
    # Create snapshot
    AnalyticsCacheService.create_analytics_snapshot(project, snapshot_type)
    
    return Response({'message': 'Analytics snapshot created successfully'})


class AnalyticsSnapshotListView(generics.ListAPIView):
    """List analytics snapshots for trend analysis"""
    serializer_class = AnalyticsSnapshotSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        project_id = self.request.query_params.get('project_id')
        snapshot_type = self.request.query_params.get('type', 'daily')
        days = int(self.request.query_params.get('days', 30))
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        queryset = AnalyticsSnapshot.objects.select_related('project')
        
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            if not project.team.members.filter(user=user, is_active=True).exists():
                return AnalyticsSnapshot.objects.none()
            queryset = queryset.filter(project=project)
        else:
            user_projects = Project.objects.filter(
                team__members__user=user,
                team__members__is_active=True
            ).distinct()
            queryset = queryset.filter(project__in=user_projects)
        
        return queryset.filter(
            snapshot_type=snapshot_type,
            snapshot_date__range=[start_date, end_date]
        ).order_by('-snapshot_date')
