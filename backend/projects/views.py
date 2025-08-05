from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Team, Project, TeamMember, Sprint
from .serializers import TeamSerializer, ProjectSerializer, SprintSerializer
from users.permissions import (
    IsTeamOwnerOrAdmin, CanModifyProject, CanManageTeamMembers,
    IsProjectOwnerOrTeamOwner, IsOwnerOrReadOnly
)
from django.contrib.auth import get_user_model

User = get_user_model()

class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Team.objects.filter(members__user=self.request.user).distinct()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsTeamOwnerOrAdmin]
        elif self.action == 'add_member':
            self.permission_classes = [CanManageTeamMembers]
        return super().get_permissions()

    def perform_create(self, serializer):
        team = serializer.save(created_by=self.request.user)
        TeamMember.objects.create(
            team=team,
            user=self.request.user,
            role='owner'
        )

    @action(detail=True, methods=['post'], permission_classes=[CanManageTeamMembers])
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
            return Response({'status': 'member added'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['delete'], permission_classes=[CanManageTeamMembers])
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
            return Response({'status': 'member removed'})
        except (User.DoesNotExist, TeamMember.DoesNotExist):
            return Response({'error': 'Member not found'}, status=status.HTTP_404_NOT_FOUND)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(team__members__user=self.request.user).distinct()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [CanModifyProject]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SprintViewSet(viewsets.ModelViewSet):
    serializer_class = SprintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Sprint.objects.filter(project__team__members__user=self.request.user).distinct()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsProjectOwnerOrTeamOwner]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)