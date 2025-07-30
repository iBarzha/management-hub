from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GitHubIntegrationViewSet,
    GitHubRepositoryViewSet, 
    GitHubIssueViewSet,
    GitHubCommitViewSet,
    SlackIntegrationViewSet,
    SlackChannelViewSet,
    SlackMessageViewSet,
    slack_slash_command
)

router = DefaultRouter()
router.register(r'github', GitHubIntegrationViewSet, basename='github-integration')
router.register(r'github-repositories', GitHubRepositoryViewSet, basename='github-repository')
router.register(r'github-issues', GitHubIssueViewSet, basename='github-issue')
router.register(r'github-commits', GitHubCommitViewSet, basename='github-commit')
router.register(r'slack', SlackIntegrationViewSet, basename='slack-integration')
router.register(r'slack-channels', SlackChannelViewSet, basename='slack-channel')
router.register(r'slack-messages', SlackMessageViewSet, basename='slack-message')

urlpatterns = [
    path('', include(router.urls)),
    path('slack/slash-command/', slack_slash_command, name='slack-slash-command'),
]