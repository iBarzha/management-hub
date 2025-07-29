import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Avatar,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Autocomplete,
  Alert,
  CircularProgress,
  Divider,
  Tab,
  Tabs,
  Link
} from '@mui/material';
import {
  GitHub as GitHubIcon,
  Sync as SyncIcon,
  Link as LinkIcon,
  Unlink as UnlinkIcon,
  OpenInNew as OpenInNewIcon,
  Code as CodeIcon,
  BugReport as BugReportIcon
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import api from '../services/api';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`github-tabpanel-${index}`}
      aria-labelledby={`github-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const GitHubIntegration = () => {
  const { user } = useSelector((state) => state.auth);
  const [integration, setIntegration] = useState(null);
  const [repositories, setRepositories] = useState([]);
  const [issues, setIssues] = useState([]);
  const [commits, setCommits] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);
  const [selectedRepository, setSelectedRepository] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);

  useEffect(() => {
    loadIntegration();
    loadProjects();
  }, []);

  const loadIntegration = async () => {
    try {
      const response = await api.get('/api/integrations/github/');
      if (response.data.length > 0) {
        setIntegration(response.data[0]);
        loadRepositories();
        loadIssues();
        loadCommits();
      }
    } catch (error) {
      console.error('Error loading GitHub integration:', error);
    }
  };

  const loadProjects = async () => {
    try {
      const response = await api.get('/api/projects/');
      setProjects(response.data);
    } catch (error) {
      console.error('Error loading projects:', error);
    }
  };

  const loadRepositories = async () => {
    try {
      const response = await api.get('/api/integrations/github-repositories/');
      setRepositories(response.data);
    } catch (error) {
      console.error('Error loading repositories:', error);
    }
  };

  const loadIssues = async () => {
    try {
      const response = await api.get('/api/integrations/github-issues/');
      setIssues(response.data);
    } catch (error) {
      console.error('Error loading issues:', error);
    }
  };

  const loadCommits = async () => {
    try {
      const response = await api.get('/api/integrations/github-commits/');
      setCommits(response.data);
    } catch (error) {
      console.error('Error loading commits:', error);
    }
  };

  const handleConnect = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Get authorization URL
      const authResponse = await api.get('/api/integrations/github/auth-url/');
      
      // Redirect to GitHub OAuth
      window.location.href = authResponse.data.auth_url;
    } catch (error) {
      setError('Failed to initiate GitHub connection');
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      setError('');
      
      await api.delete(`/api/integrations/github/${integration.id}/disconnect/`);
      
      setIntegration(null);
      setRepositories([]);
      setIssues([]);
      setCommits([]);
      setSuccess('GitHub integration disconnected successfully');
      setLoading(false);
    } catch (error) {
      setError('Failed to disconnect GitHub integration');
      setLoading(false);
    }
  };

  const handleSyncRepositories = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await api.post('/api/integrations/github-repositories/sync/');
      setRepositories(response.data.repositories);
      setSuccess(`Synced ${response.data.synced_count} repositories`);
      setLoading(false);
    } catch (error) {
      setError('Failed to sync repositories');
      setLoading(false);
    }
  };

  const handleSyncIssues = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await api.post('/api/integrations/github-issues/sync/');
      setIssues(response.data.issues);
      setSuccess(`Synced ${response.data.synced_count} issues`);
      setLoading(false);
    } catch (error) {
      setError('Failed to sync issues');
      setLoading(false);
    }
  };

  const handleSyncCommits = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await api.post('/api/integrations/github-commits/sync/');
      setCommits(response.data.commits);
      setSuccess(`Synced ${response.data.synced_count} commits`);
      setLoading(false);
    } catch (error) {
      setError('Failed to sync commits');
      setLoading(false);
    }
  };

  const handleConnectRepository = async () => {
    try {
      setLoading(true);
      setError('');
      
      await api.post(
        `/api/integrations/github-repositories/${selectedRepository.id}/connect-project/`,
        { project_id: selectedProject.id }
      );
      
      loadRepositories();
      setConnectDialogOpen(false);
      setSelectedRepository(null);
      setSelectedProject(null);
      setSuccess('Repository connected to project successfully');
      setLoading(false);
    } catch (error) {
      setError('Failed to connect repository to project');
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (!integration) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <GitHubIcon sx={{ mr: 2, fontSize: 40 }} />
            <Typography variant="h5">GitHub Integration</Typography>
          </Box>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Typography variant="body1" color="text.secondary" paragraph>
            Connect your GitHub account to sync repositories, issues, and commits with your projects.
          </Typography>
          
          <Button
            variant="contained"
            startIcon={<GitHubIcon />}
            onClick={handleConnect}
            disabled={loading}
          >
            {loading ? <CircularProgress size={20} /> : 'Connect GitHub'}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Box display="flex" alignItems="center">
              <Avatar src={integration.avatar_url} sx={{ mr: 2 }}>
                <GitHubIcon />
              </Avatar>
              <Box>
                <Typography variant="h6">{integration.name || integration.login}</Typography>
                <Typography variant="body2" color="text.secondary">
                  @{integration.login}
                </Typography>
              </Box>
            </Box>
            <Button
              variant="outlined"
              color="error"
              startIcon={<UnlinkIcon />}
              onClick={handleDisconnect}
              disabled={loading}
            >
              Disconnect
            </Button>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={4}>
              <Box textAlign="center">
                <Typography variant="h6">{integration.public_repos}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Repositories
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box textAlign="center">
                <Typography variant="h6">{integration.followers}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Followers
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box textAlign="center">
                <Typography variant="h6">{integration.following}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Following
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab label="Repositories" />
            <Tab label="Issues" />
            <Tab label="Commits" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
            <Typography variant="h6">Repositories</Typography>
            <Button
              variant="contained"
              startIcon={<SyncIcon />}
              onClick={handleSyncRepositories}
              disabled={loading}
            >
              Sync Repositories
            </Button>
          </Box>

          <List>
            {repositories.map((repo) => (
              <ListItem key={repo.id}>
                <ListItemAvatar>
                  <Avatar>
                    <CodeIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={repo.full_name}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {repo.description}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1} mt={1}>
                        {repo.language && (
                          <Chip label={repo.language} size="small" />
                        )}
                        <Chip label={`⭐ ${repo.stargazers_count}`} size="small" />
                        <Chip label={`🍴 ${repo.forks_count}`} size="small" />
                      </Box>
                    </Box>
                  }
                />
                <Box>
                  <IconButton
                    onClick={() => {
                      setSelectedRepository(repo);
                      setConnectDialogOpen(true);
                    }}
                    title="Connect to Project"
                  >
                    <LinkIcon />
                  </IconButton>
                  <IconButton
                    onClick={() => window.open(repo.html_url, '_blank')}
                    title="Open in GitHub"
                  >
                    <OpenInNewIcon />
                  </IconButton>
                </Box>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
            <Typography variant="h6">Issues</Typography>
            <Button
              variant="contained"
              startIcon={<SyncIcon />}
              onClick={handleSyncIssues}
              disabled={loading}
            >
              Sync Issues
            </Button>
          </Box>

          <List>
            {issues.map((issue) => (
              <ListItem key={issue.id}>
                <ListItemAvatar>
                  <Avatar>
                    <BugReportIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={`#${issue.number}: ${issue.title}`}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {issue.body.substring(0, 100)}...
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1} mt={1}>
                        <Chip
                          label={issue.state}
                          size="small"
                          color={issue.state === 'open' ? 'success' : 'default'}
                        />
                        {issue.labels.map((label) => (
                          <Chip key={label} label={label} size="small" />
                        ))}
                      </Box>
                    </Box>
                  }
                />
                <IconButton
                  onClick={() => window.open(issue.html_url, '_blank')}
                  title="Open in GitHub"
                >
                  <OpenInNewIcon />
                </IconButton>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
            <Typography variant="h6">Recent Commits</Typography>
            <Button
              variant="contained"
              startIcon={<SyncIcon />}
              onClick={handleSyncCommits}
              disabled={loading}
            >
              Sync Commits
            </Button>
          </Box>

          <List>
            {commits.slice(0, 20).map((commit) => (
              <ListItem key={commit.id}>
                <ListItemText
                  primary={commit.message.split('\n')[0]}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {commit.author_name} • {formatDate(commit.github_created_at)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        +{commit.additions} -{commit.deletions}
                      </Typography>
                    </Box>
                  }
                />
                <IconButton
                  onClick={() => window.open(commit.html_url, '_blank')}
                  title="Open in GitHub"
                >
                  <OpenInNewIcon />
                </IconButton>
              </ListItem>
            ))}
          </List>
        </TabPanel>
      </Card>

      {/* Connect Repository Dialog */}
      <Dialog open={connectDialogOpen} onClose={() => setConnectDialogOpen(false)}>
        <DialogTitle>Connect Repository to Project</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Connect "{selectedRepository?.full_name}" to a project to enable issue and commit tracking.
          </Typography>
          <Autocomplete
            options={projects}
            getOptionLabel={(option) => option.name}
            value={selectedProject}
            onChange={(event, newValue) => setSelectedProject(newValue)}
            renderInput={(params) => (
              <TextField {...params} label="Select Project" fullWidth />
            )}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConnectDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleConnectRepository}
            variant="contained"
            disabled={!selectedProject || loading}
          >
            Connect
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GitHubIntegration;