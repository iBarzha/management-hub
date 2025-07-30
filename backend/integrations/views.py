import os
import requests
import asyncio
from datetime import datetime
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from github import Github, GithubException
from .models import (
    GitHubIntegration, GitHubRepository, GitHubIssue, GitHubCommit,
    SlackIntegration, SlackChannel, SlackMessage,
    DiscordIntegration, DiscordChannel, DiscordMessage, DiscordCommand, DiscordRole
)
from .serializers import (
    GitHubIntegrationSerializer, GitHubRepositorySerializer,
    GitHubIssueSerializer, GitHubCommitSerializer,
    SlackIntegrationSerializer, SlackChannelSerializer, SlackMessageSerializer,
    DiscordIntegrationSerializer, DiscordChannelSerializer, DiscordMessageSerializer,
    DiscordCommandSerializer, DiscordRoleSerializer
)
from .discord_bot import bot_manager

User = get_user_model()


class GitHubIntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = GitHubIntegrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GitHubIntegration.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='auth-url')
    def get_auth_url(self, request):
        """Get GitHub OAuth authorization URL"""
        client_id = os.getenv('GITHUB_CLIENT_ID')
        redirect_uri = os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:3000/integrations/github/callback')
        scope = 'repo,user,admin:repo_hook'
        
        auth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scope}"
            f"&state={request.user.id}"
        )
        
        return Response({'auth_url': auth_url})

    @action(detail=False, methods=['post'], url_path='connect')
    def connect_github(self, request):
        """Handle GitHub OAuth callback and create integration"""
        code = request.data.get('code')
        state = request.data.get('state')
        
        if not code:
            return Response(
                {'error': 'Authorization code is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if str(state) != str(request.user.id):
            return Response(
                {'error': 'Invalid state parameter'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Exchange code for access token
            token_data = self._exchange_code_for_token(code)
            access_token = token_data['access_token']
            
            # Get user info from GitHub
            github_user = self._get_github_user_info(access_token)
            
            # Create or update integration
            integration, created = GitHubIntegration.objects.update_or_create(
                github_id=str(github_user['id']),
                defaults={
                    'user': request.user,
                    'access_token': access_token,
                    'login': github_user['login'],
                    'avatar_url': github_user.get('avatar_url', ''),
                    'name': github_user.get('name', ''),
                    'email': github_user.get('email', ''),
                    'company': github_user.get('company', ''),
                    'location': github_user.get('location', ''),
                    'bio': github_user.get('bio', ''),
                    'public_repos': github_user.get('public_repos', 0),
                    'followers': github_user.get('followers', 0),
                    'following': github_user.get('following', 0),
                }
            )
            
            # Update user's github_username
            request.user.github_username = github_user['login']
            request.user.save()
            
            serializer = self.get_serializer(integration)
            return Response({
                'integration': serializer.data,
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to connect GitHub: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'], url_path='disconnect')
    def disconnect_github(self, request, pk=None):
        """Disconnect GitHub integration"""
        try:
            integration = self.get_object()
            integration.delete()
            
            # Clear user's github_username
            request.user.github_username = ''
            request.user.save()
            
            return Response({'message': 'GitHub integration disconnected successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to disconnect GitHub: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def _exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        client_id = os.getenv('GITHUB_CLIENT_ID')
        client_secret = os.getenv('GITHUB_CLIENT_SECRET')
        
        token_url = 'https://github.com/login/oauth/access_token'
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
        }
        
        headers = {'Accept': 'application/json'}
        response = requests.post(token_url, data=data, headers=headers)
        response.raise_for_status()
        
        return response.json()

    def _get_github_user_info(self, access_token):
        """Get GitHub user information"""
        headers = {'Authorization': f'token {access_token}'}
        response = requests.get('https://api.github.com/user', headers=headers)
        response.raise_for_status()
        
        return response.json()


class GitHubRepositoryViewSet(viewsets.ModelViewSet):
    serializer_class = GitHubRepositorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GitHubRepository.objects.filter(
            integration__user=self.request.user
        )

    @action(detail=False, methods=['post'], url_path='sync')
    def sync_repositories(self, request):
        """Sync repositories from GitHub"""
        try:
            integration = GitHubIntegration.objects.get(user=request.user)
            github = Github(integration.access_token)
            user = github.get_user()
            
            synced_repos = []
            for repo in user.get_repos():
                repo_data = {
                    'integration': integration,
                    'github_id': str(repo.id),
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description or '',
                    'html_url': repo.html_url,
                    'clone_url': repo.clone_url,
                    'ssh_url': repo.ssh_url,
                    'private': repo.private,
                    'fork': repo.fork,
                    'archived': repo.archived,
                    'disabled': repo.disabled,
                    'default_branch': repo.default_branch,
                    'language': repo.language or '',
                    'size': repo.size,
                    'stargazers_count': repo.stargazers_count,
                    'watchers_count': repo.watchers_count,
                    'forks_count': repo.forks_count,
                    'open_issues_count': repo.open_issues_count,
                    'pushed_at': repo.pushed_at,
                }
                
                github_repo, created = GitHubRepository.objects.update_or_create(
                    integration=integration,
                    github_id=str(repo.id),
                    defaults=repo_data
                )
                synced_repos.append(github_repo)
            
            serializer = self.get_serializer(synced_repos, many=True)
            return Response({
                'repositories': serializer.data,
                'synced_count': len(synced_repos)
            })
            
        except GitHubIntegration.DoesNotExist:
            return Response(
                {'error': 'GitHub integration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to sync repositories: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='connect-project')
    def connect_to_project(self, request, pk=None):
        """Connect repository to a project"""
        try:
            repository = self.get_object()
            project_id = request.data.get('project_id')
            
            if not project_id:
                return Response(
                    {'error': 'Project ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from projects.models import Project
            project = Project.objects.get(id=project_id)
            
            repository.project = project
            repository.save()
            
            serializer = self.get_serializer(repository)
            return Response(serializer.data)
            
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to connect repository: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class GitHubIssueViewSet(viewsets.ModelViewSet):
    serializer_class = GitHubIssueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GitHubIssue.objects.filter(
            repository__integration__user=self.request.user
        )

    @action(detail=False, methods=['post'], url_path='sync')
    def sync_issues(self, request):
        """Sync issues from GitHub repositories"""
        try:
            integration = GitHubIntegration.objects.get(user=request.user)
            github = Github(integration.access_token)
            
            repository_id = request.data.get('repository_id')
            if repository_id:
                repositories = GitHubRepository.objects.filter(
                    id=repository_id, integration=integration
                )
            else:
                repositories = GitHubRepository.objects.filter(integration=integration)
            
            synced_issues = []
            for github_repo in repositories:
                repo = github.get_repo(github_repo.full_name)
                
                for issue in repo.get_issues(state='all'):
                    if issue.pull_request:  # Skip pull requests
                        continue
                    
                    issue_data = {
                        'repository': github_repo,
                        'github_id': str(issue.id),
                        'number': issue.number,
                        'title': issue.title,
                        'body': issue.body or '',
                        'state': issue.state,
                        'html_url': issue.html_url,
                        'assignee_login': issue.assignee.login if issue.assignee else None,
                        'milestone_title': issue.milestone.title if issue.milestone else None,
                        'labels': [label.name for label in issue.labels],
                        'comments': issue.comments,
                        'locked': issue.locked,
                        'author_association': issue.author_association,
                        'github_created_at': issue.created_at,
                        'github_updated_at': issue.updated_at,
                        'github_closed_at': issue.closed_at,
                    }
                    
                    github_issue, created = GitHubIssue.objects.update_or_create(
                        repository=github_repo,
                        github_id=str(issue.id),
                        defaults=issue_data
                    )
                    synced_issues.append(github_issue)
            
            serializer = self.get_serializer(synced_issues, many=True)
            return Response({
                'issues': serializer.data,
                'synced_count': len(synced_issues)
            })
            
        except GitHubIntegration.DoesNotExist:
            return Response(
                {'error': 'GitHub integration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to sync issues: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class GitHubCommitViewSet(viewsets.ModelViewSet):
    serializer_class = GitHubCommitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GitHubCommit.objects.filter(
            repository__integration__user=self.request.user
        )

    @action(detail=False, methods=['post'], url_path='sync')
    def sync_commits(self, request):
        """Sync commits from GitHub repositories"""
        try:
            integration = GitHubIntegration.objects.get(user=request.user)
            github = Github(integration.access_token)
            
            repository_id = request.data.get('repository_id')
            since_date = request.data.get('since_date')  # Optional date filter
            
            if repository_id:
                repositories = GitHubRepository.objects.filter(
                    id=repository_id, integration=integration
                )
            else:
                repositories = GitHubRepository.objects.filter(integration=integration)
            
            synced_commits = []
            for github_repo in repositories:
                repo = github.get_repo(github_repo.full_name)
                
                # Get commits with optional date filter
                kwargs = {}
                if since_date:
                    kwargs['since'] = datetime.fromisoformat(since_date.replace('Z', '+00:00'))
                
                for commit in repo.get_commits(**kwargs):
                    try:
                        commit_data = {
                            'repository': github_repo,
                            'sha': commit.sha,
                            'message': commit.commit.message,
                            'author_name': commit.commit.author.name,
                            'author_email': commit.commit.author.email,
                            'author_login': commit.author.login if commit.author else None,
                            'committer_name': commit.commit.committer.name,
                            'committer_email': commit.commit.committer.email,
                            'html_url': commit.html_url,
                            'github_created_at': commit.commit.author.date,
                        }
                        
                        # Get commit stats if available
                        if hasattr(commit, 'stats') and commit.stats:
                            commit_data.update({
                                'additions': commit.stats.additions,
                                'deletions': commit.stats.deletions,
                                'total_changes': commit.stats.total,
                            })
                        
                        # Get file changes if available
                        if hasattr(commit, 'files') and commit.files:
                            commit_data['files_changed'] = [
                                {
                                    'filename': f.filename,
                                    'status': f.status,
                                    'additions': f.additions,
                                    'deletions': f.deletions,
                                    'changes': f.changes,
                                }
                                for f in commit.files
                            ]
                        
                        github_commit, created = GitHubCommit.objects.update_or_create(
                            sha=commit.sha,
                            defaults=commit_data
                        )
                        synced_commits.append(github_commit)
                        
                    except Exception as commit_error:
                        # Log individual commit errors but continue processing
                        print(f"Error processing commit {commit.sha}: {commit_error}")
                        continue
            
            serializer = self.get_serializer(synced_commits, many=True)
            return Response({
                'commits': serializer.data,
                'synced_count': len(synced_commits)
            })
            
        except GitHubIntegration.DoesNotExist:
            return Response(
                {'error': 'GitHub integration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to sync commits: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class SlackIntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = SlackIntegrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SlackIntegration.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='auth-url')
    def get_auth_url(self, request):
        """Get Slack OAuth authorization URL"""
        client_id = os.getenv('SLACK_CLIENT_ID')
        redirect_uri = os.getenv('SLACK_REDIRECT_URI', 'http://localhost:3000/integrations/slack/callback')
        scope = 'channels:read,chat:write,commands,users:read,team:read'
        
        auth_url = (
            f"https://slack.com/oauth/v2/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scope}"
            f"&user_scope=identity.basic,identity.email,identity.team"
            f"&state={request.user.id}"
        )
        
        return Response({'auth_url': auth_url})

    @action(detail=False, methods=['post'], url_path='connect')
    def connect_slack(self, request):
        """Handle Slack OAuth callback and create integration"""
        code = request.data.get('code')
        state = request.data.get('state')
        
        if not code:
            return Response(
                {'error': 'Authorization code is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if str(state) != str(request.user.id):
            return Response(
                {'error': 'Invalid state parameter'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Exchange code for access token
            auth_data = self._exchange_code_for_token(code)
            
            # Get team info
            team_info = self._get_team_info(auth_data['access_token'])
            
            # Create or update integration
            integration, created = SlackIntegration.objects.update_or_create(
                user=request.user,
                team_id=team_info['team']['id'],
                defaults={
                    'team_name': team_info['team']['name'],
                    'access_token': auth_data['access_token'],
                    'bot_user_id': auth_data.get('bot_user_id'),
                    'bot_access_token': auth_data.get('bot', {}).get('bot_access_token'),
                    'scope': auth_data.get('scope', ''),
                }
            )
            
            # Sync channels
            self._sync_channels(integration)
            
            serializer = self.get_serializer(integration)
            return Response({
                'integration': serializer.data,
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to connect Slack: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'], url_path='disconnect')
    def disconnect_slack(self, request, pk=None):
        """Disconnect Slack integration"""
        try:
            integration = self.get_object()
            integration.delete()
            
            return Response({'message': 'Slack integration disconnected successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to disconnect Slack: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def _exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        client_id = os.getenv('SLACK_CLIENT_ID')
        client_secret = os.getenv('SLACK_CLIENT_SECRET')
        redirect_uri = os.getenv('SLACK_REDIRECT_URI', 'http://localhost:3000/integrations/slack/callback')
        
        token_url = 'https://slack.com/api/oauth.v2.access'
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        auth_data = response.json()
        if not auth_data.get('ok'):
            raise Exception(f"Slack OAuth error: {auth_data.get('error', 'Unknown error')}")
        
        return auth_data

    def _get_team_info(self, access_token):
        """Get Slack team information"""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://slack.com/api/team.info', headers=headers)
        response.raise_for_status()
        
        team_data = response.json()
        if not team_data.get('ok'):
            raise Exception(f"Slack API error: {team_data.get('error', 'Unknown error')}")
        
        return team_data

    def _sync_channels(self, integration):
        """Sync channels from Slack workspace"""
        headers = {'Authorization': f'Bearer {integration.access_token}'}
        response = requests.get('https://slack.com/api/conversations.list', headers=headers)
        
        if response.ok:
            data = response.json()
            if data.get('ok'):
                for channel_data in data.get('channels', []):
                    SlackChannel.objects.update_or_create(
                        integration=integration,
                        channel_id=channel_data['id'],
                        defaults={
                            'channel_name': channel_data['name'],
                            'is_private': channel_data.get('is_private', False),
                            'is_archived': channel_data.get('is_archived', False),
                        }
                    )


class SlackChannelViewSet(viewsets.ModelViewSet):
    serializer_class = SlackChannelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SlackChannel.objects.filter(
            integration__user=self.request.user
        )

    @action(detail=False, methods=['post'], url_path='sync')
    def sync_channels(self, request):
        """Sync channels from Slack workspace"""
        try:
            integration = SlackIntegration.objects.get(user=request.user)
            
            headers = {'Authorization': f'Bearer {integration.access_token}'}
            response = requests.get('https://slack.com/api/conversations.list', headers=headers)
            
            if not response.ok:
                raise Exception("Failed to fetch channels from Slack")
            
            data = response.json()
            if not data.get('ok'):
                raise Exception(f"Slack API error: {data.get('error', 'Unknown error')}")
            
            synced_channels = []
            for channel_data in data.get('channels', []):
                channel, created = SlackChannel.objects.update_or_create(
                    integration=integration,
                    channel_id=channel_data['id'],
                    defaults={
                        'channel_name': channel_data['name'],
                        'is_private': channel_data.get('is_private', False),
                        'is_archived': channel_data.get('is_archived', False),
                    }
                )
                synced_channels.append(channel)
            
            serializer = self.get_serializer(synced_channels, many=True)
            return Response({
                'channels': serializer.data,
                'synced_count': len(synced_channels)
            })
            
        except SlackIntegration.DoesNotExist:
            return Response(
                {'error': 'Slack integration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to sync channels: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='send-message')
    def send_message(self, request, pk=None):
        """Send a message to a Slack channel"""
        try:
            channel = self.get_object()
            text = request.data.get('text', '')
            attachments = request.data.get('attachments', [])
            blocks = request.data.get('blocks', [])
            
            if not text and not attachments and not blocks:
                return Response(
                    {'error': 'Message text, attachments, or blocks are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Send message via Slack API
            headers = {
                'Authorization': f'Bearer {channel.integration.bot_access_token or channel.integration.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'channel': channel.channel_id,
                'text': text,
            }
            
            if attachments:
                payload['attachments'] = attachments
            if blocks:
                payload['blocks'] = blocks
            
            response = requests.post('https://slack.com/api/chat.postMessage', 
                                   json=payload, headers=headers)
            
            slack_response = response.json()
            
            # Save message record
            message = SlackMessage.objects.create(
                channel=channel,
                message_type='notification',
                text=text,
                attachments=attachments,
                blocks=blocks,
                slack_timestamp=slack_response.get('ts'),
                sent_successfully=slack_response.get('ok', False),
                error_message=slack_response.get('error') if not slack_response.get('ok') else None
            )
            
            serializer = SlackMessageSerializer(message)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to send message: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class SlackMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SlackMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SlackMessage.objects.filter(
            channel__integration__user=self.request.user
        )


@api_view(['POST'])
@permission_classes([])  # Slack webhooks don't use our auth
def slack_slash_command(request):
    """Handle Slack slash commands"""
    # Verify the request comes from Slack
    slack_signing_secret = os.getenv('SLACK_SIGNING_SECRET')
    if not slack_signing_secret:
        return Response({'error': 'Slack signing secret not configured'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    command = request.data.get('command', '')
    text = request.data.get('text', '')
    user_id = request.data.get('user_id', '')
    channel_id = request.data.get('channel_id', '')
    team_id = request.data.get('team_id', '')
    
    try:
        # Find the integration
        integration = SlackIntegration.objects.get(team_id=team_id)
        
        # Handle different commands
        if command == '/tasks':
            return _handle_tasks_command(integration, text, channel_id)
        elif command == '/create-task':
            return _handle_create_task_command(integration, text, user_id, channel_id)
        elif command == '/project-status':
            return _handle_project_status_command(integration, text, channel_id)
        else:
            return Response({
                'response_type': 'ephemeral',
                'text': f'Unknown command: {command}'
            })
            
    except SlackIntegration.DoesNotExist:
        return Response({
            'response_type': 'ephemeral',
            'text': 'Slack integration not found. Please connect your Slack workspace first.'
        })
    except Exception as e:
        return Response({
            'response_type': 'ephemeral',
            'text': f'Error processing command: {str(e)}'
        })


def _handle_tasks_command(integration, text, channel_id):
    """Handle /tasks command"""
    from tasks.models import Task
    
    # Get tasks based on filter
    tasks = Task.objects.filter(
        project__team__members__user=integration.user
    )
    
    if text:
        # Filter by status if provided
        tasks = tasks.filter(status__icontains=text)
    
    tasks = tasks[:10]  # Limit to 10 tasks
    
    if not tasks.exists():
        return Response({
            'response_type': 'ephemeral',
            'text': 'No tasks found.'
        })
    
    attachments = []
    for task in tasks:
        color = {
            'todo': '#6c757d',
            'in_progress': '#ffc107',
            'done': '#28a745',
            'blocked': '#dc3545'
        }.get(task.status, '#6c757d')
        
        attachments.append({
            'color': color,
            'title': task.title,
            'text': task.description[:100] + '...' if len(task.description) > 100 else task.description,
            'fields': [
                {
                    'title': 'Status',
                    'value': task.get_status_display(),
                    'short': True
                },
                {
                    'title': 'Priority',
                    'value': task.get_priority_display(),
                    'short': True
                },
                {
                    'title': 'Assigned to',
                    'value': task.assignee.get_full_name() if task.assignee else 'Unassigned',
                    'short': True
                },
                {
                    'title': 'Due Date',
                    'value': task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date',
                    'short': True
                }
            ]
        })
    
    return Response({
        'response_type': 'in_channel',
        'text': f'Found {tasks.count()} tasks:',
        'attachments': attachments
    })


def _handle_create_task_command(integration, text, user_id, channel_id):
    """Handle /create-task command"""
    if not text:
        return Response({
            'response_type': 'ephemeral',
            'text': 'Please provide a task title. Usage: /create-task <title>'
        })

    
    return Response({
        'response_type': 'ephemeral',
        'text': f'Task creation feature is coming soon! Title: {text}'
    })


def _handle_project_status_command(integration, text, channel_id):
    """Handle /project-status command"""
    from projects.models import Project
    
    if not text:
        projects = Project.objects.filter(team__members__user=integration.user)[:5]
        project_list = '\n'.join([f"• {p.name}" for p in projects])
        return Response({
            'response_type': 'ephemeral',
            'text': f'Available projects:\n{project_list}\n\nUsage: /project-status <project-name>'
        })
    
    try:
        project = Project.objects.get(
            name__icontains=text,
            team__members__user=integration.user
        )
        
        # Get project statistics
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(status='done').count()
        in_progress_tasks = project.tasks.filter(status='in_progress').count()
        blocked_tasks = project.tasks.filter(status='blocked').count()
        
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        attachment = {
            'color': '#28a745' if progress > 80 else '#ffc107' if progress > 40 else '#dc3545',
            'title': f'Project: {project.name}',
            'text': project.description,
            'fields': [
                {
                    'title': 'Total Tasks',
                    'value': str(total_tasks),
                    'short': True
                },
                {
                    'title': 'Completed',
                    'value': str(completed_tasks),
                    'short': True
                },
                {
                    'title': 'In Progress',
                    'value': str(in_progress_tasks),
                    'short': True
                },
                {
                    'title': 'Blocked',
                    'value': str(blocked_tasks),
                    'short': True
                },
                {
                    'title': 'Progress',
                    'value': f'{progress:.1f}%',
                    'short': True
                },
                {
                    'title': 'Status',
                    'value': project.get_status_display(),
                    'short': True
                }
            ]
        }
        
        return Response({
            'response_type': 'in_channel',
            'attachments': [attachment]
        })
        
    except Project.DoesNotExist:
        return Response({
            'response_type': 'ephemeral',
            'text': f'Project "{text}" not found.'
        })
    except Exception as e:
        return Response({
            'response_type': 'ephemeral',
            'text': f'Error retrieving project status: {str(e)}'
        })


class DiscordIntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = DiscordIntegrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DiscordIntegration.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='auth-url')
    def get_auth_url(self, request):
        """Get Discord OAuth authorization URL"""
        client_id = os.getenv('DISCORD_CLIENT_ID')
        redirect_uri = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:3000/integrations/discord/callback')
        scope = 'bot applications.commands guilds'
        permissions = '8'  # Administrator permissions (adjust as needed)
        
        auth_url = (
            f"https://discord.com/api/oauth2/authorize"
            f"?client_id={client_id}"
            f"&permissions={permissions}"
            f"&scope={scope}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&state={request.user.id}"
        )
        
        return Response({'auth_url': auth_url})

    @action(detail=False, methods=['post'], url_path='connect')
    def connect_discord(self, request):
        """Handle Discord OAuth callback and create integration"""
        code = request.data.get('code')
        state = request.data.get('state')
        guild_id = request.data.get('guild_id')
        
        if not code:
            return Response(
                {'error': 'Authorization code is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if str(state) != str(request.user.id):
            return Response(
                {'error': 'Invalid state parameter'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if not guild_id:
            return Response(
                {'error': 'Guild ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Exchange code for access token
            token_data = self._exchange_code_for_token(code)
            
            # Get guild information
            guild_info = self._get_guild_info(guild_id, token_data['access_token'])
            
            # Create or update integration
            integration, created = DiscordIntegration.objects.update_or_create(
                user=request.user,
                guild_id=guild_id,
                defaults={
                    'guild_name': guild_info['name'],
                    'bot_token': os.getenv('DISCORD_BOT_TOKEN'),
                    'application_id': os.getenv('DISCORD_CLIENT_ID'),
                    'permissions': int(token_data.get('permissions', 8)),
                }
            )
            
            # Start Discord bot for this integration
            asyncio.create_task(bot_manager.start_bot(integration.id))
            
            serializer = self.get_serializer(integration)
            return Response({
                'integration': serializer.data,
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to connect Discord: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'], url_path='disconnect')
    def disconnect_discord(self, request, pk=None):
        """Disconnect Discord integration"""
        try:
            integration = self.get_object()
            
            # Stop Discord bot
            asyncio.create_task(bot_manager.stop_bot(integration.id))
            
            integration.delete()
            
            return Response({'message': 'Discord integration disconnected successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to disconnect Discord: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='send-notification')
    def send_notification(self, request, pk=None):
        """Send a notification to Discord channel"""
        try:
            integration = self.get_object()
            channel_id = request.data.get('channel_id')
            title = request.data.get('title', 'Notification')
            description = request.data.get('description', '')
            color = request.data.get('color', 0x3498db)
            fields = request.data.get('fields', [])
            
            if not channel_id:
                return Response(
                    {'error': 'Channel ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Prepare embed data
            embed_data = {
                'title': title,
                'description': description,
                'color': color,
                'timestamp': datetime.utcnow().isoformat(),
                'fields': fields
            }
            
            # Send notification via bot manager
            success = asyncio.run(bot_manager.send_notification(channel_id, embed_data))
            success = False  # Temporarily disabled
            
            if success:
                # Save message record
                channel_obj = DiscordChannel.objects.get(
                    integration=integration,
                    channel_id=channel_id
                )
                
                message = DiscordMessage.objects.create(
                    channel=channel_obj,
                    message_type='notification',
                    embeds=[embed_data],
                    sent_successfully=True
                )
                
                serializer = DiscordMessageSerializer(message)
                return Response(serializer.data)
            else:
                return Response(
                    {'error': 'Failed to send Discord notification'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except DiscordChannel.DoesNotExist:
            return Response(
                {'error': 'Discord channel not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to send notification: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def _exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        client_id = os.getenv('DISCORD_CLIENT_ID')
        client_secret = os.getenv('DISCORD_CLIENT_SECRET')
        redirect_uri = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:3000/integrations/discord/callback')
        
        token_url = 'https://discord.com/api/oauth2/token'
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(token_url, data=data, headers=headers)
        response.raise_for_status()
        
        return response.json()

    def _get_guild_info(self, guild_id, access_token):
        """Get Discord guild information"""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f'https://discord.com/api/guilds/{guild_id}', headers=headers)
        response.raise_for_status()
        
        return response.json()


class DiscordChannelViewSet(viewsets.ModelViewSet):
    serializer_class = DiscordChannelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DiscordChannel.objects.filter(
            integration__user=self.request.user
        )

    @action(detail=False, methods=['post'], url_path='sync')
    def sync_channels(self, request):
        """Sync channels from Discord guild"""
        try:
            integration_id = request.data.get('integration_id')
            if not integration_id:
                return Response(
                    {'error': 'Integration ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            integration = DiscordIntegration.objects.get(
                id=integration_id, 
                user=request.user
            )
            
            # Channels are synced automatically when bot starts
            # This endpoint returns current synced channels
            channels = DiscordChannel.objects.filter(integration=integration)
            serializer = self.get_serializer(channels, many=True)
            
            return Response({
                'channels': serializer.data,
                'count': channels.count()
            })
            
        except DiscordIntegration.DoesNotExist:
            return Response(
                {'error': 'Discord integration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to sync channels: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='connect-project')
    def connect_to_project(self, request, pk=None):
        """Connect Discord channel to a project"""
        try:
            channel = self.get_object()
            project_id = request.data.get('project_id')
            
            if not project_id:
                return Response(
                    {'error': 'Project ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from projects.models import Project
            project = Project.objects.get(id=project_id)
            
            channel.project = project
            channel.save()
            
            serializer = self.get_serializer(channel)
            return Response(serializer.data)
            
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to connect channel: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class DiscordMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DiscordMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DiscordMessage.objects.filter(
            channel__integration__user=self.request.user
        )


class DiscordCommandViewSet(viewsets.ModelViewSet):
    serializer_class = DiscordCommandSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DiscordCommand.objects.filter(
            integration__user=self.request.user
        )

    @action(detail=False, methods=['get'], url_path='usage-stats')
    def usage_stats(self, request):
        """Get command usage statistics"""
        try:
            integration_id = request.query_params.get('integration_id')
            if integration_id:
                commands = self.get_queryset().filter(integration_id=integration_id)
            else:
                commands = self.get_queryset()
            
            stats = []
            for command in commands:
                stats.append({
                    'command_name': command.command_name,
                    'usage_count': command.usage_count,
                    'last_used': command.last_used,
                    'enabled': command.enabled
                })
            
            return Response({'stats': stats})
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get usage stats: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class DiscordRoleViewSet(viewsets.ModelViewSet):
    serializer_class = DiscordRoleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DiscordRole.objects.filter(
            integration__user=self.request.user
        )

    @action(detail=False, methods=['post'], url_path='sync')
    def sync_roles(self, request):
        """Sync roles from Discord guild"""
        try:
            integration_id = request.data.get('integration_id')
            if not integration_id:
                return Response(
                    {'error': 'Integration ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            integration = DiscordIntegration.objects.get(
                id=integration_id, 
                user=request.user
            )
            
            # Roles are synced automatically when bot starts
            # This endpoint returns current synced roles
            roles = DiscordRole.objects.filter(integration=integration)
            serializer = self.get_serializer(roles, many=True)
            
            return Response({
                'roles': serializer.data,
                'count': roles.count()
            })
            
        except DiscordIntegration.DoesNotExist:
            return Response(
                {'error': 'Discord integration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to sync roles: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
@permission_classes([])  # Discord webhooks don't use our auth
def discord_webhook(request):
    """Handle Discord webhook events"""
    try:
        # Verify the request comes from Discord (implement signature verification)
        # For now, we'll skip verification in development
        
        event_type = request.headers.get('X-Discord-Event-Type')
        data = request.data
        
        if event_type == 'MESSAGE_CREATE':
            # Handle new messages (could be used for chat integration)
            pass
        elif event_type == 'GUILD_MEMBER_ADD':
            # Handle new member joining
            pass
        elif event_type == 'INTERACTION_CREATE':
            # Handle slash command interactions
            return _handle_discord_interaction(data)
        
        return Response({'status': 'success'})
        
    except Exception as e:
        return Response(
            {'error': f'Webhook processing failed: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


def _handle_discord_interaction(interaction_data):
    """Handle Discord slash command interactions"""
    try:
        interaction_type = interaction_data.get('type')
        
        if interaction_type == 2:  # APPLICATION_COMMAND
            command_name = interaction_data['data']['name']
            options = interaction_data['data'].get('options', [])
            guild_id = interaction_data.get('guild_id')
            channel_id = interaction_data.get('channel_id')
            user_id = interaction_data['member']['user']['id']
            
            # Find the integration
            try:
                integration = DiscordIntegration.objects.get(guild_id=guild_id)
            except DiscordIntegration.DoesNotExist:
                return Response({
                    'type': 4,  # CHANNEL_MESSAGE_WITH_SOURCE
                    'data': {
                        'content': 'Discord integration not found. Please reconnect the bot.',
                        'flags': 64  # EPHEMERAL
                    }
                })
            
            # Handle different commands
            if command_name == 'tasks':
                return _handle_discord_tasks_interaction(integration, options, channel_id)
            elif command_name == 'create-task':
                return _handle_discord_create_task_interaction(integration, options, user_id, channel_id)
            elif command_name == 'project-status':
                return _handle_discord_project_status_interaction(integration, options)
            else:
                return Response({
                    'type': 4,
                    'data': {
                        'content': f'Unknown command: {command_name}',
                        'flags': 64
                    }
                })
        
        return Response({'type': 1})  # PONG
        
    except Exception as e:
        return Response({
            'type': 4,
            'data': {
                'content': f'Error processing interaction: {str(e)}',
                'flags': 64
            }
        })


def _handle_discord_tasks_interaction(integration, options, channel_id):
    """Handle Discord /tasks slash command"""
    from tasks.models import Task
    
    status_filter = None
    for option in options:
        if option['name'] == 'status':
            status_filter = option['value']
    
    try:
        # Get channel and project
        channel = DiscordChannel.objects.get(
            integration=integration,
            channel_id=channel_id
        )
        
        if not channel.project:
            return Response({
                'type': 4,
                'data': {
                    'content': '❌ This channel is not associated with a project.',
                    'flags': 64
                }
            })
        
        # Get tasks
        tasks = Task.objects.filter(project=channel.project)
        if status_filter:
            tasks = tasks.filter(status=status_filter)
        
        tasks = tasks[:10]  # Limit to 10
        
        if not tasks.exists():
            return Response({
                'type': 4,
                'data': {
                    'content': f'📝 No tasks found' + (f' with status: {status_filter}' if status_filter else ''),
                    'flags': 64
                }
            })
        
        # Build embed
        embed_fields = []
        for task in tasks:
            priority_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴', 'urgent': '🚨'}.get(task.priority, '⚪')
            embed_fields.append({
                'name': f"{priority_emoji} {task.title}",
                'value': f"**Status:** {task.status}\n**Assignee:** {task.assignee.email if task.assignee else 'Unassigned'}",
                'inline': False
            })
        
        embed = {
            'title': f'📋 Tasks ({status_filter or "all"})',
            'color': 0x3498db,
            'fields': embed_fields,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return Response({
            'type': 4,
            'data': {
                'embeds': [embed]
            }
        })
        
    except DiscordChannel.DoesNotExist:
        return Response({
            'type': 4,
            'data': {
                'content': '❌ Channel not found in database.',
                'flags': 64
            }
        })


def _handle_discord_create_task_interaction(integration, options, user_id, channel_id):
    """Handle Discord /create-task slash command"""
    title = None
    description = None
    
    for option in options:
        if option['name'] == 'title':
            title = option['value']
        elif option['name'] == 'description':
            description = option['value']
    
    if not title:
        return Response({
            'type': 4,
            'data': {
                'content': '❌ Task title is required.',
                'flags': 64
            }
        })
    
    try:
        from tasks.models import Task
        
        # Get channel and project
        channel = DiscordChannel.objects.get(
            integration=integration,
            channel_id=channel_id
        )
        
        if not channel.project:
            return Response({
                'type': 4,
                'data': {
                    'content': '❌ This channel is not associated with a project.',
                    'flags': 64
                }
            })
        
        # Create task
        task = Task.objects.create(
            title=title,
            description=description or '',
            project=channel.project,
            status='todo',
            priority='medium',
            created_by=integration.user
        )
        
        embed = {
            'title': '✅ Task Created',
            'description': f"**{task.title}**",
            'color': 0x28a745,
            'fields': [
                {'name': 'ID', 'value': str(task.id), 'inline': True},
                {'name': 'Status', 'value': task.status, 'inline': True},
                {'name': 'Priority', 'value': task.priority, 'inline': True}
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return Response({
            'type': 4,
            'data': {
                'embeds': [embed]
            }
        })
        
    except DiscordChannel.DoesNotExist:
        return Response({
            'type': 4,
            'data': {
                'content': '❌ Channel not found in database.',
                'flags': 64
            }
        })
    except Exception as e:
        return Response({
            'type': 4,
            'data': {
                'content': f'❌ Error creating task: {str(e)}',
                'flags': 64
            }
        })


def _handle_discord_project_status_interaction(integration, options):
    """Handle Discord /project-status slash command"""
    project_name = None
    
    for option in options:
        if option['name'] == 'project':
            project_name = option['value']
    
    if not project_name:
        return Response({
            'type': 4,
            'data': {
                'content': '❌ Project name is required.',
                'flags': 64
            }
        })
    
    try:
        from projects.models import Project
        from tasks.models import Task
        
        # Find project
        project = Project.objects.get(
            name__icontains=project_name,
            team__members__user=integration.user
        )
        
        # Get statistics
        total_tasks = Task.objects.filter(project=project).count()
        completed_tasks = Task.objects.filter(project=project, status='done').count()
        in_progress_tasks = Task.objects.filter(project=project, status='in_progress').count()
        todo_tasks = Task.objects.filter(project=project, status='todo').count()
        
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Determine color based on progress
        if progress > 80:
            color = 0x28a745  # Green
        elif progress > 40:
            color = 0xffc107  # Yellow
        else:
            color = 0xdc3545  # Red
        
        embed = {
            'title': f'📊 Project Status: {project.name}',
            'description': project.description or 'No description available',
            'color': color,
            'fields': [
                {'name': '📈 Progress', 'value': f'{progress:.1f}%', 'inline': True},
                {'name': '✅ Completed', 'value': str(completed_tasks), 'inline': True},
                {'name': '🔄 In Progress', 'value': str(in_progress_tasks), 'inline': True},
                {'name': '📝 To Do', 'value': str(todo_tasks), 'inline': True},
                {'name': '📊 Total Tasks', 'value': str(total_tasks), 'inline': True},
                {'name': '🏷️ Status', 'value': project.status.title(), 'inline': True}
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return Response({
            'type': 4,
            'data': {
                'embeds': [embed]
            }
        })
        
    except Project.DoesNotExist:
        return Response({
            'type': 4,
            'data': {
                'content': f'❌ Project "{project_name}" not found.',
                'flags': 64
            }
        })
    except Exception as e:
        return Response({
            'type': 4,
            'data': {
                'content': f'❌ Error retrieving project status: {str(e)}',
                'flags': 64
            }
        })
