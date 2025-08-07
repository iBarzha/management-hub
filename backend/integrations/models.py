from django.db import models
from django.contrib.auth import get_user_model
from projects.models import Project
from tasks.models import Task

User = get_user_model()


class GitHubIntegration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='github_integration')
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    github_id = models.CharField(max_length=100, unique=True)
    login = models.CharField(max_length=100)
    avatar_url = models.URLField(blank=True, null=True)
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True, null=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    public_repos = models.IntegerField(default=0)
    followers = models.IntegerField(default=0)
    following = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'github_integrations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.login}"


class GitHubRepository(models.Model):
    integration = models.ForeignKey(GitHubIntegration, on_delete=models.CASCADE, related_name='repositories')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='github_repositories', null=True, blank=True)
    github_id = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=400)
    description = models.TextField(blank=True, null=True)
    html_url = models.URLField()
    clone_url = models.URLField()
    ssh_url = models.CharField(max_length=500)
    private = models.BooleanField(default=False)
    fork = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    disabled = models.BooleanField(default=False)
    default_branch = models.CharField(max_length=100, default='main')
    language = models.CharField(max_length=100, blank=True, null=True)
    size = models.IntegerField(default=0)
    stargazers_count = models.IntegerField(default=0)
    watchers_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    open_issues_count = models.IntegerField(default=0)
    pushed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'github_repositories'
        unique_together = ['integration', 'github_id']
        ordering = ['-updated_at']

    def __str__(self):
        return self.full_name


class GitHubIssue(models.Model):
    ISSUE_STATE_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]

    repository = models.ForeignKey(GitHubRepository, on_delete=models.CASCADE, related_name='issues')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='github_issues', null=True, blank=True)
    github_id = models.CharField(max_length=100)
    number = models.IntegerField()
    title = models.CharField(max_length=500)
    body = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=20, choices=ISSUE_STATE_CHOICES, default='open')
    html_url = models.URLField()
    assignee_login = models.CharField(max_length=100, blank=True, null=True)
    milestone_title = models.CharField(max_length=200, blank=True, null=True)
    labels = models.JSONField(default=list)
    comments = models.IntegerField(default=0)
    locked = models.BooleanField(default=False)
    author_association = models.CharField(max_length=50, blank=True, null=True)
    github_created_at = models.DateTimeField()
    github_updated_at = models.DateTimeField()
    github_closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'github_issues'
        unique_together = ['repository', 'github_id']
        ordering = ['-github_updated_at']

    def __str__(self):
        return f"#{self.number}: {self.title}"


class GitHubCommit(models.Model):
    repository = models.ForeignKey(GitHubRepository, on_delete=models.CASCADE, related_name='commits')
    sha = models.CharField(max_length=40, unique=True)
    message = models.TextField()
    author_name = models.CharField(max_length=200)
    author_email = models.EmailField()
    author_login = models.CharField(max_length=100, blank=True, null=True)
    committer_name = models.CharField(max_length=200)
    committer_email = models.EmailField()
    html_url = models.URLField()
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)
    total_changes = models.IntegerField(default=0)
    files_changed = models.JSONField(default=list)
    github_created_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'github_commits'
        ordering = ['-github_created_at']

    def __str__(self):
        return f"{self.sha[:8]}: {self.message[:50]}"


class GitHubWebhook(models.Model):
    WEBHOOK_EVENT_CHOICES = [
        ('push', 'Push'),
        ('pull_request', 'Pull Request'),
        ('issues', 'Issues'),
        ('issue_comment', 'Issue Comment'),
        ('commit_comment', 'Commit Comment'),
        ('create', 'Create'),
        ('delete', 'Delete'),
        ('release', 'Release'),
    ]

    repository = models.ForeignKey(GitHubRepository, on_delete=models.CASCADE, related_name='webhooks')
    github_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100, default='web')
    active = models.BooleanField(default=True)
    events = models.JSONField(default=list)
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'github_webhooks'
        unique_together = ['repository', 'github_id']
        ordering = ['-created_at']

    def __str__(self):
        return f"Webhook for {self.repository.full_name}"


class SlackIntegration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='slack_integration')
    team_id = models.CharField(max_length=100)
    team_name = models.CharField(max_length=200)
    access_token = models.TextField()
    bot_user_id = models.CharField(max_length=100, blank=True, null=True)
    bot_access_token = models.TextField(blank=True, null=True)
    webhook_url = models.URLField(blank=True, null=True)
    scope = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'slack_integrations'
        unique_together = ['user', 'team_id']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.team_name}"


class SlackChannel(models.Model):
    integration = models.ForeignKey(SlackIntegration, on_delete=models.CASCADE, related_name='channels')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='slack_channels', null=True, blank=True)
    channel_id = models.CharField(max_length=100)
    channel_name = models.CharField(max_length=200)
    is_private = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    notifications_enabled = models.BooleanField(default=True)
    notification_types = models.JSONField(default=list)  # ['task_created', 'task_updated', 'deadline_reminder', etc.]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'slack_channels'
        unique_together = ['integration', 'channel_id']
        ordering = ['channel_name']

    def __str__(self):
        return f"#{self.channel_name}"


class SlackMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('notification', 'Notification'),
        ('command_response', 'Command Response'),
        ('webhook', 'Webhook'),
    ]

    channel = models.ForeignKey(SlackChannel, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='notification')
    slack_timestamp = models.CharField(max_length=20, blank=True, null=True)
    text = models.TextField()
    attachments = models.JSONField(default=list)
    blocks = models.JSONField(default=list)
    user_id = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=200, blank=True, null=True)
    sent_successfully = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'slack_messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"Message to #{self.channel.channel_name}: {self.text[:50]}"


class DiscordIntegration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='discord_integration')
    guild_id = models.CharField(max_length=100)
    guild_name = models.CharField(max_length=200)
    bot_token = models.TextField()
    application_id = models.CharField(max_length=100)
    permissions = models.BigIntegerField(default=0)
    webhook_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'discord_integrations'
        unique_together = ['user', 'guild_id']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.guild_name}"


class DiscordChannel(models.Model):
    CHANNEL_TYPE_CHOICES = [
        ('text', 'Text Channel'),
        ('voice', 'Voice Channel'),
        ('category', 'Category'),
        ('news', 'News Channel'),
        ('stage', 'Stage Channel'),
        ('forum', 'Forum Channel'),
    ]

    integration = models.ForeignKey(DiscordIntegration, on_delete=models.CASCADE, related_name='channels')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='discord_channels', null=True, blank=True)
    channel_id = models.CharField(max_length=100, unique=True)
    channel_name = models.CharField(max_length=200)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPE_CHOICES, default='text')
    parent_id = models.CharField(max_length=100, blank=True, null=True)
    position = models.IntegerField(default=0)
    nsfw = models.BooleanField(default=False)
    notifications_enabled = models.BooleanField(default=True)
    notification_types = models.JSONField(default=list)  # ['task_created', 'task_updated', 'deadline_reminder', etc.]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'discord_channels'
        unique_together = ['integration', 'channel_id']
        ordering = ['position', 'channel_name']

    def __str__(self):
        return f"#{self.channel_name}"


class DiscordMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('notification', 'Notification'),
        ('command_response', 'Command Response'),
        ('webhook', 'Webhook'),
        ('embed', 'Rich Embed'),
    ]

    channel = models.ForeignKey(DiscordChannel, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='notification')
    discord_message_id = models.CharField(max_length=100, blank=True, null=True)
    content = models.TextField(blank=True)
    embeds = models.JSONField(default=list)
    components = models.JSONField(default=list)  # Buttons, select menus, etc.
    attachments = models.JSONField(default=list)
    user_id = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=200, blank=True, null=True)
    sent_successfully = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'discord_messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"Message to #{self.channel.channel_name}: {self.content[:50] if self.content else 'Embed'}"


class DiscordCommand(models.Model):
    COMMAND_TYPE_CHOICES = [
        ('slash', 'Slash Command'),
        ('prefix', 'Prefix Command'),
        ('context', 'Context Menu'),
    ]

    integration = models.ForeignKey(DiscordIntegration, on_delete=models.CASCADE, related_name='commands')
    command_name = models.CharField(max_length=100)
    command_type = models.CharField(max_length=20, choices=COMMAND_TYPE_CHOICES, default='slash')
    description = models.TextField()
    enabled = models.BooleanField(default=True)
    permissions_required = models.JSONField(default=list)  # ['manage_tasks', 'view_projects', etc.]
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'discord_commands'
        unique_together = ['integration', 'command_name']
        ordering = ['command_name']

    def __str__(self):
        return f"/{self.command_name}"


class DiscordRole(models.Model):
    integration = models.ForeignKey(DiscordIntegration, on_delete=models.CASCADE, related_name='roles')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='discord_roles', null=True, blank=True)
    role_id = models.CharField(max_length=100, unique=True)
    role_name = models.CharField(max_length=200)
    color = models.CharField(max_length=7, default='#000000')  # Hex color
    permissions = models.BigIntegerField(default=0)
    position = models.IntegerField(default=0)
    mentionable = models.BooleanField(default=False)
    hoisted = models.BooleanField(default=False)
    managed = models.BooleanField(default=False)
    sync_with_project_role = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'discord_roles'
        unique_together = ['integration', 'role_id']
        ordering = ['-position', 'role_name']

    def __str__(self):
        return f"@{self.role_name}"


class GoogleCalendarIntegration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='google_calendar_integration')
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    calendar_id = models.CharField(max_length=500, default='primary')
    google_user_email = models.EmailField(blank=True, null=True)
    scope = models.TextField(default='https://www.googleapis.com/auth/calendar')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'google_calendar_integrations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - Google Calendar"


class CalendarEvent(models.Model):
    EVENT_STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('tentative', 'Tentative'),
        ('cancelled', 'Cancelled'),
    ]

    TRANSPARENCY_CHOICES = [
        ('opaque', 'Busy'),
        ('transparent', 'Free'),
    ]

    integration = models.ForeignKey(GoogleCalendarIntegration, on_delete=models.CASCADE, related_name='events')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='calendar_events', null=True, blank=True)
    google_event_id = models.CharField(max_length=1024, unique=True)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=500, blank=True, null=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    timezone = models.CharField(max_length=100, default='UTC')
    all_day = models.BooleanField(default=False)
    recurring = models.BooleanField(default=False)
    recurrence_rule = models.TextField(blank=True, null=True)  # RRULE
    status = models.CharField(max_length=20, choices=EVENT_STATUS_CHOICES, default='confirmed')
    transparency = models.CharField(max_length=20, choices=TRANSPARENCY_CHOICES, default='opaque')
    attendees = models.JSONField(default=list)  # List of attendee objects
    creator_email = models.EmailField(blank=True, null=True)
    organizer_email = models.EmailField(blank=True, null=True)
    hangout_link = models.URLField(blank=True, null=True)
    meeting_url = models.URLField(blank=True, null=True)
    visibility = models.CharField(max_length=20, default='default')  # default, public, private
    reminders = models.JSONField(default=list)  # List of reminder objects
    google_created_at = models.DateTimeField()
    google_updated_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calendar_events'
        ordering = ['start_datetime']

    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"


class MeetingSchedule(models.Model):
    MEETING_TYPE_CHOICES = [
        ('standup', 'Daily Standup'),
        ('planning', 'Sprint Planning'),
        ('review', 'Sprint Review'),
        ('retrospective', 'Sprint Retrospective'),
        ('general', 'General Meeting'),
        ('one_on_one', 'One-on-One'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='meetings')
    calendar_event = models.OneToOneField(CalendarEvent, on_delete=models.CASCADE, related_name='meeting_schedule', null=True, blank=True)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE_CHOICES, default='general')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    timezone = models.CharField(max_length=100, default='UTC')
    location = models.CharField(max_length=500, blank=True, null=True)
    meeting_url = models.URLField(blank=True, null=True)
    attendees = models.ManyToManyField(User, related_name='scheduled_meetings', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_meetings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    recurring = models.BooleanField(default=False)
    recurrence_pattern = models.JSONField(default=dict)  # Custom recurrence data
    agenda = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    action_items = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meeting_schedules'
        ordering = ['start_datetime']

    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"


class CalendarSync(models.Model):
    SYNC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    integration = models.ForeignKey(GoogleCalendarIntegration, on_delete=models.CASCADE, related_name='sync_records')
    sync_type = models.CharField(max_length=50, default='full')  # full, incremental, events_only
    status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    events_synced = models.IntegerField(default=0)
    events_created = models.IntegerField(default=0)
    events_updated = models.IntegerField(default=0)
    events_deleted = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    sync_token = models.CharField(max_length=500, blank=True, null=True)  # For incremental sync
    
    class Meta:
        db_table = 'calendar_sync_records'
        ordering = ['-started_at']

    def __str__(self):
        return f"Sync {self.id} - {self.status} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
