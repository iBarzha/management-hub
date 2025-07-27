from rest_framework import serializers
from .models import Task, TaskComment, TaskAttachment
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


class TaskCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    task_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TaskComment
        fields = ['id', 'task_id', 'author', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    task_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TaskAttachment
        fields = ['id', 'task_id', 'uploaded_by', 'file_name', 'file_url',
                  'file_size', 'file_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class TaskDetailSerializer(TaskSerializer):
    comments = TaskCommentSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    attachment_count = serializers.SerializerMethodField()

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['comments', 'attachments', 'comment_count', 'attachment_count']

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_attachment_count(self, obj):
        return obj.attachments.count()