import os
import requests
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
    SlackIntegration, SlackChannel, SlackMessage
)
from .serializers import (
    GitHubIntegrationSerializer, GitHubRepositorySerializer,
    GitHubIssueSerializer, GitHubCommitSerializer,
    SlackIntegrationSerializer, SlackChannelSerializer, SlackMessageSerializer
)

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
