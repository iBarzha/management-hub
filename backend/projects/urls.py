from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeamViewSet, ProjectViewSet, SprintViewSet

router = DefaultRouter()
router.register('teams', TeamViewSet, basename='team')
router.register('projects', ProjectViewSet, basename='project')
router.register('sprints', SprintViewSet, basename='sprint')

urlpatterns = [
    path('', include(router.urls)),
]