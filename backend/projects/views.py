from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Count, Q
from django.db import transaction
from .models import Team, Project, TeamMember, Sprint
from .serializers import TeamSerializer, ProjectSerializer, SprintSerializer
from users.permissions import (
    IsTeamOwnerOrAdmin, CanModifyProject, CanManageTeamMembers,
    IsProjectOwnerOrTeamOwner, IsOwnerOrReadOnly
)
from django.contrib.auth import get_user_model
from config.cache_utils import CacheManager, cache_result
from config.pagination import EnhancedPageNumberPagination, ProjectPagination

User = get_user_model()

class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = EnhancedPageNumberPagination

    def get_queryset(self):
        cache_key = CacheManager.get_team_cache_key(self.request.user.id)
        cached_teams = cache.get(cache_key)
        
        if cached_teams is None:
            teams = Team.objects.filter(
                members__user=self.request.user
            ).select_related('created_by').prefetch_related(
                'members__user',
                'projects'  # Prefetch projects to avoid extra queries
            ).annotate(
                member_count=Count('members', distinct=True),
                project_count=Count('projects', distinct=True)
            ).distinct()
            cache.set(cache_key, teams, 300)  # Cache for 5 minutes
            return teams
        
        return cached_teams

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsTeamOwnerOrAdmin]
        elif self.action == 'add_member':
            self.permission_classes = [CanManageTeamMembers]
        return super().get_permissions()

    @transaction.atomic
    def perform_create(self, serializer):
        team = serializer.save(created_by=self.request.user)
        TeamMember.objects.create(
            team=team,
            user=self.request.user,
            role='owner'
        )
        # Capture user ID for callback (request context will be lost)
        user_id = self.request.user.id
        # Schedule cache invalidation to happen after transaction commits
        transaction.on_commit(lambda: self._invalidate_team_cache_for_user(user_id))

    def _invalidate_team_cache_for_user(self, user_id):
        """Helper method to invalidate team cache after transaction commits"""
        cache_key = CacheManager.get_team_cache_key(user_id)
        cache.delete(cache_key)
        CacheManager.invalidate_user_cache(user_id)

    @action(detail=True, methods=['post'], permission_classes=[CanManageTeamMembers])
    @transaction.atomic
    def add_member(self, request, pk=None):
        team = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'member')

        # Only owners can add other owners
        if role == 'owner':
            try:
                membership = TeamMember.objects.get(team=team, user=request.user)
                if membership.role != 'owner':
                    return Response(
                        {'error': 'Only team owners can add other owners'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except TeamMember.DoesNotExist:
                return Response(
                    {'error': 'You are not a member of this team'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

        try:
            user = User.objects.get(id=user_id)
            TeamMember.objects.create(team=team, user=user, role=role)
            # Invalidate cache for both users
            CacheManager.invalidate_user_cache(request.user.id)
            CacheManager.invalidate_user_cache(user.id)
            return Response({'status': 'member added'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['delete'], permission_classes=[CanManageTeamMembers])
    @transaction.atomic
    def remove_member(self, request, pk=None):
        team = self.get_object()
        user_id = request.data.get('user_id')

        try:
            user = User.objects.get(id=user_id)
            membership = TeamMember.objects.get(team=team, user=user)
            
            # Prevent removing the last owner
            if membership.role == 'owner':
                owner_count = TeamMember.objects.filter(team=team, role='owner').count()
                if owner_count <= 1:
                    return Response(
                        {'error': 'Cannot remove the last owner of the team'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            membership.delete()
            # Invalidate cache for both users
            CacheManager.invalidate_user_cache(request.user.id)
            CacheManager.invalidate_user_cache(user.id)
            return Response({'status': 'member removed'})
        except (User.DoesNotExist, TeamMember.DoesNotExist):
            return Response({'error': 'Member not found'}, status=status.HTTP_404_NOT_FOUND)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ProjectPagination

    def get_queryset(self):
        cache_key = CacheManager.get_projects_cache_key(self.request.user.id)
        cached_projects = cache.get(cache_key)
        
        if cached_projects is None:
            projects = Project.objects.filter(
                team__members__user=self.request.user
            ).select_related('team', 'created_by').prefetch_related(
                'team__members__user',
                'tasks',  # Prefetch tasks for counts
                'sprints'  # Prefetch sprints for counts
            ).annotate(
                task_count=Count('tasks', distinct=True),
                completed_task_count=Count('tasks', filter=Q(tasks__status='done'), distinct=True),
                sprint_count=Count('sprints', distinct=True)
            ).distinct()
            cache.set(cache_key, projects, 300)  # Cache for 5 minutes
            return projects
        
        return cached_projects

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [CanModifyProject]
        return super().get_permissions()

    def perform_create(self, serializer):
        project = serializer.save(created_by=self.request.user)
        # Capture user ID for callback (request context will be lost)
        user_id = self.request.user.id
        # Schedule cache invalidation to happen after transaction commits
        transaction.on_commit(lambda: self._invalidate_project_cache_for_user(user_id))
        return project

    def _invalidate_project_cache_for_user(self, user_id):
        """Helper method to invalidate project cache after transaction commits"""
        cache_key = CacheManager.get_projects_cache_key(user_id)
        cache.delete(cache_key)
        CacheManager.invalidate_user_cache(user_id)


class SprintViewSet(viewsets.ModelViewSet):
    serializer_class = SprintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Sprint.objects.filter(
            project__team__members__user=self.request.user
        ).select_related('project', 'project__team', 'created_by').distinct()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsProjectOwnerOrTeamOwner]
        return super().get_permissions()

    def perform_create(self, serializer):
        sprint = serializer.save(created_by=self.request.user)
        # Invalidate project-related cache
        CacheManager.invalidate_project_cache(sprint.project.id)
        return sprint