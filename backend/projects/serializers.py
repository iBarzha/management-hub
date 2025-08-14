from rest_framework import serializers
from .models import Team, TeamMember, Project, Sprint
from users.serializers import UserSerializer
from users.validators import CustomValidationMixin, SQLInjectionValidator


class TeamMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TeamMember
        fields = ['id', 'user', 'role', 'joined_at']


class TeamSerializer(CustomValidationMixin, serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members = TeamMemberSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_by', 'members',
                  'member_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate and sanitize team name."""
        if value:
            SQLInjectionValidator.validate_input(value)
            return self.validate_text_field(value, 'name', max_length=100)
        return value
    
    def validate_description(self, value):
        """Validate and sanitize team description."""
        return self.validate_text_field(value, 'description', max_length=1000)

    def get_member_count(self, obj):
        # Use annotated value if available, otherwise count
        return getattr(obj, 'member_count', obj.members.count())


class ProjectSerializer(CustomValidationMixin, serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    team_id = serializers.IntegerField(write_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'team', 'team_id', 'status',
                  'start_date', 'end_date', 'cover_image', 'github_repo_url',
                  'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate and sanitize project name."""
        if value:
            SQLInjectionValidator.validate_input(value)
            return self.validate_text_field(value, 'name', max_length=200)
        return value
    
    def validate_description(self, value):
        """Validate and sanitize project description."""
        return self.validate_html_field(value, 'description', max_length=2000)
    
    def validate_cover_image(self, value):
        """Validate cover image URL."""
        return self.validate_url_field(value)
    
    def validate_github_repo_url(self, value):
        """Validate GitHub repository URL."""
        return self.validate_url_field(value)


class SprintSerializer(CustomValidationMixin, serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    project_id = serializers.IntegerField(write_only=True)
    created_by = UserSerializer(read_only=True)
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Sprint
        fields = ['id', 'name', 'description', 'project', 'project_id', 'status',
                  'start_date', 'end_date', 'goal', 'created_by', 'task_count',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate and sanitize sprint name."""
        if value:
            SQLInjectionValidator.validate_input(value)
            return self.validate_text_field(value, 'name', max_length=200)
        return value
    
    def validate_description(self, value):
        """Validate and sanitize sprint description."""
        return self.validate_html_field(value, 'description', max_length=1000)
    
    def validate_goal(self, value):
        """Validate and sanitize sprint goal."""
        return self.validate_html_field(value, 'goal', max_length=1000)

    def get_task_count(self, obj):
        # Use annotated value if available, otherwise count
        return getattr(obj, 'task_count', obj.tasks.count())