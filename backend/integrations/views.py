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
from .models import GitHubIntegration, GitHubRepository, GitHubIssue, GitHubCommit
from .serializers import (
    GitHubIntegrationSerializer, GitHubRepositorySerializer,
    GitHubIssueSerializer, GitHubCommitSerializer
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
