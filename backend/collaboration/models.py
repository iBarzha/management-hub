from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.message[:50]}'


class RoomParticipant(models.Model):
    room = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['room', 'user']
        ordering = ['-last_seen']

    def __str__(self):
        return f'{self.user.username} in {self.room}'


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_updated', 'Task Updated'),
        ('project_updated', 'Project Updated'),
        ('sprint_started', 'Sprint Started'),
        ('sprint_ended', 'Sprint Ended'),
        ('deadline_reminder', 'Deadline Reminder'),
        ('comment_added', 'Comment Added'),
        ('mention', 'Mention'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional foreign keys for context
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True, blank=True)
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.user.username}'


class UserPresence(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    current_project = models.ForeignKey('projects.Project', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-last_seen']
    
    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        return f'{self.user.username} - {status}'
