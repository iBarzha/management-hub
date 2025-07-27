from rest_framework import serializers
from .models import Team, TeamMember, Project, Sprint
from users.serializers import UserSerializer


class TeamMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TeamMember
        fields = ['id', 'user', 'role', 'joined_at']


class TeamSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members = TeamMemberSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_by', 'members',
                  'member_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.members.count()


class ProjectSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    team_id = serializers.IntegerField(write_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'team', 'team_id', 'status',
                  'start_date', 'end_date', 'cover_image', 'github_repo_url',
                  'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SprintSerializer(serializers.ModelSerializer):
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

    def get_task_count(self, obj):
        return obj.tasks.count()