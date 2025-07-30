from rest_framework import serializers
from .models import (
    GitHubIntegration, GitHubRepository, GitHubIssue, GitHubCommit, GitHubWebhook,
    SlackIntegration, SlackChannel, SlackMessage
)


class GitHubIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubIntegration
        fields = [
            'id', 'github_id', 'login', 'avatar_url', 'name', 'email',
            'company', 'location', 'bio', 'public_repos', 'followers', 
            'following', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GitHubRepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubRepository
        fields = [
            'id', 'github_id', 'name', 'full_name', 'description', 'html_url',
            'clone_url', 'ssh_url', 'private', 'fork', 'archived', 'disabled',
            'default_branch', 'language', 'size', 'stargazers_count', 
            'watchers_count', 'forks_count', 'open_issues_count', 'pushed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GitHubIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubIssue
        fields = [
            'id', 'github_id', 'number', 'title', 'body', 'state', 'html_url',
            'assignee_login', 'milestone_title', 'labels', 'comments', 'locked',
            'author_association', 'github_created_at', 'github_updated_at',
            'github_closed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GitHubCommitSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubCommit
        fields = [
            'id', 'sha', 'message', 'author_name', 'author_email', 'author_login',
            'committer_name', 'committer_email', 'html_url', 'additions',
            'deletions', 'total_changes', 'files_changed', 'github_created_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GitHubWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubWebhook
        fields = [
            'id', 'github_id', 'name', 'active', 'events', 'config',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SlackIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackIntegration
        fields = [
            'id', 'team_id', 'team_name', 'bot_user_id', 'webhook_url', 'scope',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SlackChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackChannel
        fields = [
            'id', 'channel_id', 'channel_name', 'is_private', 'is_archived',
            'notifications_enabled', 'notification_types', 'project',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SlackMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackMessage
        fields = [
            'id', 'message_type', 'slack_timestamp', 'text', 'attachments',
            'blocks', 'user_id', 'username', 'sent_successfully', 'error_message',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']