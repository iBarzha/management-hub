from rest_framework import permissions
from projects.models import TeamMember, Project
from tasks.models import Task


class BaseTeamPermission(permissions.BasePermission):
    """Base permission class for team-based access control."""
    
    def has_team_permission(self, request, view, team, required_roles=None):
        """Check if user has required role in team."""
        if not request.user.is_authenticated:
            return False
            
        if request.user.is_superuser:
            return True
            
        try:
            membership = TeamMember.objects.get(team=team, user=request.user)
            if required_roles:
                return membership.role in required_roles
            return True
        except TeamMember.DoesNotExist:
            return False


class IsTeamOwnerOrAdmin(BaseTeamPermission):
    """Permission that only allows team owners or admins to access."""
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'team'):
            team = obj.team
        elif hasattr(obj, 'project') and hasattr(obj.project, 'team'):
            team = obj.project.team
        else:
            return False
            
        return self.has_team_permission(request, view, team, ['owner', 'admin'])


class IsTeamMemberOrReadOnly(BaseTeamPermission):
    """Permission that allows team members to read/write, others read only."""
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'team'):
            team = obj.team
        elif hasattr(obj, 'project') and hasattr(obj.project, 'team'):
            team = obj.project.team
        else:
            return False
            
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions only for team members
        return self.has_team_permission(request, view, team)


class CanModifyProject(BaseTeamPermission):
    """Permission for project modification based on role."""
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Project):
            project = obj
        else:
            return False
            
        team = project.team
        
        # Read permissions for team members
        if request.method in permissions.SAFE_METHODS:
            return self.has_team_permission(request, view, team)
            
        # Write permissions for owners and admins
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return self.has_team_permission(request, view, team, ['owner', 'admin'])
            
        return False


class CanModifyTask(BaseTeamPermission):
    """Permission for task modification based on role and assignment."""
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Task):
            task = obj
        else:
            return False
            
        team = task.project.team
        
        # Read permissions for team members
        if request.method in permissions.SAFE_METHODS:
            return self.has_team_permission(request, view, team)
            
        # Task assignee can modify their own tasks
        if task.assignee == request.user:
            return True
            
        # Owners and admins can modify any task
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return self.has_team_permission(request, view, team, ['owner', 'admin'])
            
        return False


class CanCreateTask(BaseTeamPermission):
    """Permission for task creation."""
    
    def has_permission(self, request, view):
        if request.method == 'POST' and 'project' in request.data:
            try:
                project = Project.objects.get(id=request.data['project'])
                team = project.team
                # Members and above can create tasks
                return self.has_team_permission(request, view, team, ['owner', 'admin', 'member'])
            except Project.DoesNotExist:
                return False
        return True


class IsProjectOwnerOrTeamOwner(BaseTeamPermission):
    """Permission for project owners or team owners/admins."""
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Project):
            project = obj
        else:
            return False
            
        # Project creator has full access
        if project.created_by == request.user:
            return True
            
        # Team owners and admins have access
        team = project.team
        return self.has_team_permission(request, view, team, ['owner', 'admin'])


class CanViewTeamAnalytics(BaseTeamPermission):
    """Permission for viewing team analytics - members and above."""
    
    def has_permission(self, request, view):
        team_id = view.kwargs.get('team_id') or request.query_params.get('team_id')
        if team_id:
            try:
                from projects.models import Team
                team = Team.objects.get(id=team_id)
                return self.has_team_permission(request, view, team, ['owner', 'admin', 'member'])
            except Team.DoesNotExist:
                return False
        return True


class CanManageTeamMembers(BaseTeamPermission):
    """Permission for managing team members - owners and admins only."""
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'team'):
            team = obj.team
            return self.has_team_permission(request, view, team, ['owner', 'admin'])
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission that only allows owners of an object to edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions only for the owner
        return obj.created_by == request.user or request.user.is_superuser