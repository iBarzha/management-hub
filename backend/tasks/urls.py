from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskCommentViewSet, TaskAttachmentViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'task-comments', TaskCommentViewSet, basename='taskcomment')
router.register(r'task-attachments', TaskAttachmentViewSet, basename='taskattachment')

urlpatterns = [
    path('', include(router.urls)),
]