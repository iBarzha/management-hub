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
    slack_slash_command,
    DiscordIntegrationViewSet,
    DiscordChannelViewSet,
    DiscordMessageViewSet,
    DiscordCommandViewSet,
    DiscordRoleViewSet,
    discord_webhook
)

router = DefaultRouter()
router.register(r'github', GitHubIntegrationViewSet, basename='github-integration')
router.register(r'github-repositories', GitHubRepositoryViewSet, basename='github-repository')
router.register(r'github-issues', GitHubIssueViewSet, basename='github-issue')
router.register(r'github-commits', GitHubCommitViewSet, basename='github-commit')
router.register(r'slack', SlackIntegrationViewSet, basename='slack-integration')
router.register(r'slack-channels', SlackChannelViewSet, basename='slack-channel')
router.register(r'slack-messages', SlackMessageViewSet, basename='slack-message')
router.register(r'discord', DiscordIntegrationViewSet, basename='discord-integration')
router.register(r'discord-channels', DiscordChannelViewSet, basename='discord-channel')
router.register(r'discord-messages', DiscordMessageViewSet, basename='discord-message')
router.register(r'discord-commands', DiscordCommandViewSet, basename='discord-command')
router.register(r'discord-roles', DiscordRoleViewSet, basename='discord-role')

urlpatterns = [
    path('', include(router.urls)),
    path('slack/slash-command/', slack_slash_command, name='slack-slash-command'),
    path('discord/webhook/', discord_webhook, name='discord-webhook'),
]