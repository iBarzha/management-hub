from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GitHubIntegrationViewSet,
    GitHubRepositoryViewSet, 
    GitHubIssueViewSet,
    GitHubCommitViewSet
)

router = DefaultRouter()
router.register(r'github', GitHubIntegrationViewSet, basename='github-integration')
router.register(r'github-repositories', GitHubRepositoryViewSet, basename='github-repository')
router.register(r'github-issues', GitHubIssueViewSet, basename='github-issue')
router.register(r'github-commits', GitHubCommitViewSet, basename='github-commit')

urlpatterns = [
    path('', include(router.urls)),
]