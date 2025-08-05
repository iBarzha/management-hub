from rest_framework import serializers
from .models import Task, TaskComment, TaskAttachment
from projects.serializers import ProjectSerializer
from users.serializers import UserSerializer
from users.validators import CustomValidationMixin, SQLInjectionValidator, SecureFileValidator


class TaskSerializer(CustomValidationMixin, serializers.ModelSerializer):
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
    
    def validate_title(self, value):
        """Validate and sanitize task title."""
        if value:
            SQLInjectionValidator.validate_input(value)
            return self.validate_text_field(value, 'title', max_length=200)
        return value
    
    def validate_description(self, value):
        """Validate and sanitize task description."""
        return self.validate_html_field(value, 'description', max_length=5000)


class TaskCommentSerializer(CustomValidationMixin, serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    task_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TaskComment
        fields = ['id', 'task_id', 'author', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_content(self, value):
        """Validate and sanitize comment content."""
        return self.validate_html_field(value, 'content', max_length=2000)


class TaskAttachmentSerializer(CustomValidationMixin, serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    task_id = serializers.IntegerField(write_only=True)
    file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = TaskAttachment
        fields = ['id', 'task_id', 'uploaded_by', 'file_name', 'file_url',
                  'file_size', 'file_type', 'file', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_file_name(self, value):
        """Validate and sanitize file name."""
        if value:
            SQLInjectionValidator.validate_input(value)
            from users.validators import InputSanitizer
            return InputSanitizer.sanitize_filename(value)
        return value
    
    def validate_file_url(self, value):
        """Validate file URL."""
        return self.validate_url_field(value)
    
    def validate_file(self, value):
        """Validate uploaded file."""
        if value:
            return SecureFileValidator.validate_file(value)
        return value


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