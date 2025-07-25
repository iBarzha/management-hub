from rest_framework import serializers
from .models import Task
from projects.serializers import ProjectSerializer
from users.serializers import UserSerializer


class TaskSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    project_id = serializers.IntegerField(write_only=True)
    assignee = UserSerializer(read_only=True)
    assignee_id = serializers.IntegerField(write_only=True, required=False)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'project', 'project_id',
                  'assignee', 'assignee_id', 'priority', 'status', 'due_date',
                  'estimated_hours', 'actual_hours', 'created_by',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']