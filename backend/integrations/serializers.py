from rest_framework import serializers
from .models import (
    GitHubIntegration, GitHubRepository, GitHubIssue, GitHubCommit, GitHubWebhook,
    SlackIntegration, SlackChannel, SlackMessage,
    DiscordIntegration, DiscordChannel, DiscordMessage, DiscordCommand, DiscordRole,
    GoogleCalendarIntegration, CalendarEvent, MeetingSchedule, CalendarSync
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


class DiscordIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordIntegration
        fields = [
            'id', 'guild_id', 'guild_name', 'application_id', 'permissions',
            'webhook_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DiscordChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordChannel
        fields = [
            'id', 'channel_id', 'channel_name', 'channel_type', 'parent_id',
            'position', 'nsfw', 'notifications_enabled', 'notification_types',
            'project', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DiscordMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordMessage
        fields = [
            'id', 'message_type', 'discord_message_id', 'content', 'embeds',
            'components', 'attachments', 'user_id', 'username', 
            'sent_successfully', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DiscordCommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordCommand
        fields = [
            'id', 'command_name', 'command_type', 'description', 'enabled',
            'permissions_required', 'usage_count', 'last_used',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'last_used', 'created_at', 'updated_at']


class DiscordRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordRole
        fields = [
            'id', 'role_id', 'role_name', 'color', 'permissions', 'position',
            'mentionable', 'hoisted', 'managed', 'sync_with_project_role',
            'project', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GoogleCalendarIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleCalendarIntegration
        fields = [
            'id', 'calendar_id', 'google_user_email', 'scope',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = [
            'id', 'google_event_id', 'title', 'description', 'location',
            'start_datetime', 'end_datetime', 'timezone', 'all_day', 'recurring',
            'recurrence_rule', 'status', 'transparency', 'attendees',
            'creator_email', 'organizer_email', 'hangout_link', 'meeting_url',
            'visibility', 'reminders', 'google_created_at', 'google_updated_at',
            'project', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'google_event_id', 'google_created_at', 'google_updated_at', 'created_at', 'updated_at']


class MeetingScheduleSerializer(serializers.ModelSerializer):
    attendees_list = serializers.SerializerMethodField()
    
    class Meta:
        model = MeetingSchedule
        fields = [
            'id', 'title', 'description', 'meeting_type', 'start_datetime',
            'end_datetime', 'timezone', 'location', 'meeting_url', 'attendees',
            'attendees_list', 'created_by', 'status', 'recurring', 'recurrence_pattern',
            'agenda', 'notes', 'action_items', 'project', 'calendar_event',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'attendees_list']

    def get_attendees_list(self, obj):
        return [
            {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name(),
            }
            for user in obj.attendees.all()
        ]


class CalendarSyncSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarSync
        fields = [
            'id', 'sync_type', 'status', 'started_at', 'completed_at',
            'events_synced', 'events_created', 'events_updated', 'events_deleted',
            'error_message', 'sync_token'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'events_synced', 'events_created', 'events_updated', 'events_deleted']