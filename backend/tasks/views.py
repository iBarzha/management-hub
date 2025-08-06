from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from .models import Task, TaskComment, TaskAttachment
from .serializers import TaskSerializer, TaskDetailSerializer, TaskCommentSerializer, TaskAttachmentSerializer
from users.permissions import CanModifyTask, CanCreateTask, IsOwnerOrReadOnly, IsTeamMemberOrReadOnly
from config.cache_utils import CacheManager
from config.pagination import TaskPagination, CommentPagination


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = TaskPagination

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        cache_key = CacheManager.get_tasks_cache_key(self.request.user.id, project_id)
        cached_tasks = cache.get(cache_key)
        
        if cached_tasks is None:
            queryset = Task.objects.filter(
                project__team__members__user=self.request.user
            ).select_related(
                'project', 'project__team', 'assignee', 'created_by', 'sprint'
            ).prefetch_related('comments', 'attachments').distinct()
            
            if project_id:
                queryset = queryset.filter(project_id=project_id)
            
            # Convert to list to cache it
            tasks = list(queryset)
            cache.set(cache_key, tasks, 300)  # Cache for 5 minutes
            return tasks
        
        return cached_tasks

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'create':
            self.permission_classes = [CanCreateTask]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [CanModifyTask]
        return super().get_permissions()

    def perform_create(self, serializer):
        task = serializer.save(created_by=self.request.user)
        # Invalidate task and project cache
        CacheManager.invalidate_user_cache(self.request.user.id)
        CacheManager.invalidate_project_cache(task.project.id)
        return task

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        task = self.get_object()
        
        if request.method == 'GET':
            comments = task.comments.select_related('author').all()
            serializer = TaskCommentSerializer(comments, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = TaskCommentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(task=task, author=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get', 'post'])
    def attachments(self, request, pk=None):
        task = self.get_object()
        
        if request.method == 'GET':
            attachments = task.attachments.select_related('uploaded_by').all()
            serializer = TaskAttachmentSerializer(attachments, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = TaskAttachmentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(task=task, uploaded_by=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CommentPagination

    def get_queryset(self):
        return TaskComment.objects.filter(
            task__project__team__members__user=self.request.user
        ).select_related('task', 'author').distinct()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOwnerOrReadOnly]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TaskAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskAttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaskAttachment.objects.filter(
            task__project__team__members__user=self.request.user
        ).select_related('task', 'uploaded_by').distinct()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOwnerOrReadOnly]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
