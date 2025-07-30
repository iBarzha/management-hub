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
