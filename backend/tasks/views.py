from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Task, TaskComment, TaskAttachment
from .serializers import TaskSerializer, TaskDetailSerializer, TaskCommentSerializer, TaskAttachmentSerializer
from users.permissions import CanModifyTask, CanCreateTask, IsOwnerOrReadOnly, IsTeamMemberOrReadOnly


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(project__team__members__user=self.request.user).distinct()

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
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        task = self.get_object()
        
        if request.method == 'GET':
            comments = task.comments.all()
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
            attachments = task.attachments.all()
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

    def get_queryset(self):
        return TaskComment.objects.filter(task__project__team__members__user=self.request.user).distinct()

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
        return TaskAttachment.objects.filter(task__project__team__members__user=self.request.user).distinct()

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOwnerOrReadOnly]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
