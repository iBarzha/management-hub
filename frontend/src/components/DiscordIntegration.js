import React, { useState, useEffect } from 'react';
import {Box, Card, CardContent, Typography, Button, Grid, Avatar, Chip, List, ListItem, ListItemText, ListItemAvatar,
  IconButton, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Autocomplete, Alert, CircularProgress,
  Tab, Tabs, FormControlLabel, Switch} from '@mui/material';
import {
  Forum as DiscordIcon,
  Sync as SyncIcon,
  Link as LinkIcon,
  LinkOff as UnlinkIcon,
  VolumeUp as VoiceIcon,
  Tag as ChannelIcon,
  PersonAdd as UserIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import api from '../services/api';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`discord-tabpanel-${index}`}
      aria-labelledby={`discord-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const DiscordIntegration = () => {
  const { user } = useSelector((state) => state.auth);
  const [integration, setIntegration] = useState(null);
  const [channels, setChannels] = useState([]);
  const [messages, setMessages] = useState([]);
  const [commands, setCommands] = useState([]);
  const [roles, setRoles] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [notificationSettings, setNotificationSettings] = useState({
    task_created: true,
    task_updated: true,
    task_assigned: true,
    task_completed: true,
    project_updated: true,
    deadline_reminder: true,
    standup_reminder: true
  });

  useEffect(() => {
    loadIntegration();
    loadProjects();
  }, []);

  const loadIntegration = async () => {
    try {
      const response = await api.get('/integrations/discord/');
      if (response.data.length > 0) {
        setIntegration(response.data[0]);
        loadChannels();
        loadMessages();
        loadCommands();
        loadRoles();
      }
    } catch (error) {
      console.error('Error loading Discord integration:', error);
    }
  };

  const loadProjects = async () => {
    try {
      const response = await api.get('/projects/');
      setProjects(response.data);
    } catch (error) {
      console.error('Error loading projects:', error);
    }
  };

  const loadChannels = async () => {
    try {
      const response = await api.get('/integrations/discord-channels/');
      setChannels(response.data);
    } catch (error) {
      console.error('Error loading channels:', error);
    }
  };

  const loadMessages = async () => {
    try {
      const response = await api.get('/integrations/discord-messages/');
      setMessages(response.data);
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const loadCommands = async () => {
    try {
      const response = await api.get('/integrations/discord-commands/');
      setCommands(response.data);
    } catch (error) {
      console.error('Error loading commands:', error);
    }
  };

  const loadRoles = async () => {
    try {
      const response = await api.get('/integrations/discord-roles/');
      setRoles(response.data);
    } catch (error) {
      console.error('Error loading roles:', error);
    }
  };

  const handleConnect = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Get authorization URL
      const authResponse = await api.get('/integrations/discord/auth-url/');
      
      // Redirect to Discord OAuth
      window.location.href = authResponse.data.auth_url;
    } catch (error) {
      setError('Failed to initiate Discord connection');
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      setError('');
      
      await api.delete(`/api/integrations/discord/${integration.id}/disconnect/`);
      
      setIntegration(null);
      setChannels([]);
      setMessages([]);
      setCommands([]);
      setRoles([]);
      setSuccess('Discord integration disconnected successfully');
      setLoading(false);
    } catch (error) {
      setError('Failed to disconnect Discord integration');
      setLoading(false);
    }
  };

  const handleSyncChannels = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await api.post('/integrations/discord-channels/sync/');
      setChannels(response.data.channels);
      setSuccess(`Synced ${response.data.synced_count} channels`);
      setLoading(false);
    } catch (error) {
      setError('Failed to sync channels');
      setLoading(false);
    }
  };

  const handleConnectChannel = async () => {
    try {
      setLoading(true);
      setError('');
      
      await api.post(
        `/api/integrations/discord-channels/${selectedChannel.id}/connect-project/`,
        { project_id: selectedProject.id }
      );
      
      loadChannels();
      setConnectDialogOpen(false);
      setSelectedChannel(null);
      setSelectedProject(null);
      setSuccess('Channel connected to project successfully');
      setLoading(false);
    } catch (error) {
      setError('Failed to connect channel to project');
      setLoading(false);
    }
  };

  const handleSendNotification = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await api.post('/integrations/discord/send-notification/', {
        channel_id: selectedChannel?.channel_id,
        message: 'Test notification from Project Management Hub! 🚀'
      });
      
      if (response.data.success) {
        setSuccess('Test notification sent successfully');
      } else {
        setError('Failed to send test notification');
      }
      setLoading(false);
    } catch (error) {
      setError('Failed to send test notification');
      setLoading(false);
    }
  };

  const handleUpdateNotificationSettings = async () => {
    try {
      setLoading(true);
      setError('');
      
      await api.patch(`/api/integrations/discord/${integration.id}/`, {
        notification_settings: notificationSettings
      });
      
      setSettingsDialogOpen(false);
      setSuccess('Notification settings updated successfully');
      setLoading(false);
    } catch (error) {
      setError('Failed to update notification settings');
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getChannelIcon = (channelType) => {
    switch (channelType) {
      case 'voice':
        return <VoiceIcon />;
      case 'text':
      default:
        return <ChannelIcon />;
    }
  };

  if (!integration) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <DiscordIcon sx={{ mr: 2, fontSize: 40, color: '#5865F2' }} />
            <Typography variant="h5">Discord Integration</Typography>
          </Box>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Typography variant="body1" color="text.secondary" paragraph>
            Connect your Discord server to enable bot commands, notifications, and project management features.
          </Typography>
          
          <Typography variant="body2" color="text.secondary" paragraph>
            Available bot commands: !tasks, !create-task, !assign, !project-status, !standup, and more!
          </Typography>
          
          <Button
            variant="contained"
            startIcon={<DiscordIcon />}
            onClick={handleConnect}
            disabled={loading}
            sx={{ bgcolor: '#5865F2', '&:hover': { bgcolor: '#4752C4' } }}
          >
            {loading ? <CircularProgress size={20} /> : 'Connect Discord'}
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
              <Avatar sx={{ mr: 2, bgcolor: '#5865F2' }}>
                <DiscordIcon />
              </Avatar>
              <Box>
                <Typography variant="h6">{integration.guild_name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Guild ID: {integration.guild_id}
                </Typography>
              </Box>
            </Box>
            <Box>
              <IconButton
                onClick={() => setSettingsDialogOpen(true)}
                title="Settings"
                sx={{ mr: 1 }}
              >
                <SettingsIcon />
              </IconButton>
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
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={3}>
              <Box textAlign="center">
                <Typography variant="h6">{channels.length}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Channels
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={3}>
              <Box textAlign="center">
                <Typography variant="h6">{roles.length}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Roles
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={3}>
              <Box textAlign="center">
                <Typography variant="h6">{commands.length}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Commands
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={3}>
              <Box textAlign="center">
                <Typography variant="h6">
                  {integration.permissions ? '✅' : '❌'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Bot Active
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
            <Tab label="Channels" />
            <Tab label="Commands" />
            <Tab label="Messages" />
            <Tab label="Roles" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Discord Channels</Typography>
            <Button
              variant="contained"
              startIcon={<SyncIcon />}
              onClick={handleSyncChannels}
              disabled={loading}
            >
              Sync Channels
            </Button>
          </Box>

          <List>
            {channels.map((channel) => (
              <ListItem key={channel.id}>
                <ListItemAvatar>
                  <Avatar>
                    {getChannelIcon(channel.channel_type)}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={`#${channel.channel_name}`}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Type: {channel.channel_type} • Position: {channel.position}
                      </Typography>
                      {channel.project && (
                        <Chip 
                          label={`Connected to: ${channel.project_name}`} 
                          size="small" 
                          color="primary"
                          sx={{ mt: 1 }}
                        />
                      )}
                      {channel.notifications_enabled && (
                        <Chip 
                          label="Notifications ON" 
                          size="small" 
                          color="success"
                          sx={{ mt: 1, ml: 1 }}
                        />
                      )}
                    </Box>
                  }
                />
                <Box>
                  <IconButton
                    onClick={() => {
                      setSelectedChannel(channel);
                      setConnectDialogOpen(true);
                    }}
                    title="Connect to Project"
                  >
                    <LinkIcon />
                  </IconButton>
                  <IconButton
                    onClick={() => {
                      setSelectedChannel(channel);
                      handleSendNotification();
                    }}
                    title="Send Test Notification"
                  >
                    <NotificationsIcon />
                  </IconButton>
                </Box>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" mb={2}>Bot Commands</Typography>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Available commands for your Discord server:
          </Typography>
          
          <List>
            {commands.map((command) => (
              <ListItem key={command.id}>
                <ListItemText
                  primary={`!${command.command_name}`}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {command.description}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1} mt={1}>
                        <Chip 
                          label={`Used ${command.usage_count} times`} 
                          size="small" 
                        />
                        <Chip 
                          label={command.enabled ? 'Enabled' : 'Disabled'} 
                          size="small" 
                          color={command.enabled ? 'success' : 'default'}
                        />
                        {command.last_used && (
                          <Chip 
                            label={`Last used: ${formatDate(command.last_used)}`} 
                            size="small" 
                          />
                        )}
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
            ))}
            
            {/* Show default commands if none loaded yet */}
            {commands.length === 0 && (
              <>
                <ListItem>
                  <ListItemText
                    primary="!tasks [status]"
                    secondary="List project tasks with optional status filter"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="!create-task <title>"
                    secondary="Create a new task in the connected project"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="!assign @user <task_id>"
                    secondary="Assign a task to a Discord user"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="!project-status <name>"
                    secondary="Get project overview and statistics"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="!standup"
                    secondary="Send daily standup reminder"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="!help-pm"
                    secondary="Show all available bot commands"
                  />
                </ListItem>
              </>
            )}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" mb={2}>Recent Messages</Typography>
          
          <List>
            {messages.slice(0, 10).map((message) => (
              <ListItem key={message.id}>
                <ListItemText
                  primary={message.content.substring(0, 100) + (message.content.length > 100 ? '...' : '')}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Channel: #{message.channel_name} • {formatDate(message.discord_created_at)}
                      </Typography>
                      {message.message_type && (
                        <Chip 
                          label={message.message_type} 
                          size="small" 
                          sx={{ mt: 1 }}
                        />
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" mb={2}>Server Roles</Typography>
          
          <List>
            {roles.map((role) => (
              <ListItem key={role.id}>
                <ListItemAvatar>
                  <Avatar 
                    sx={{ 
                      bgcolor: role.color !== '#000000' ? role.color : '#99AAB5',
                      width: 24,
                      height: 24
                    }}
                  >
                    <UserIcon sx={{ fontSize: 16 }} />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={role.role_name}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Position: {role.position}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1} mt={1}>
                        {role.mentionable && (
                          <Chip label="Mentionable" size="small" />
                        )}
                        {role.hoisted && (
                          <Chip label="Hoisted" size="small" />
                        )}
                        {role.managed && (
                          <Chip label="Bot Role" size="small" />
                        )}
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </TabPanel>
      </Card>

      {/* Connect Channel Dialog */}
      <Dialog open={connectDialogOpen} onClose={() => setConnectDialogOpen(false)}>
        <DialogTitle>Connect Channel to Project</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Connect "#{selectedChannel?.channel_name}" to a project to enable bot commands and notifications.
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
            onClick={handleConnectChannel}
            variant="contained"
            disabled={!selectedProject || loading}
          >
            Connect
          </Button>
        </DialogActions>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={settingsDialogOpen} onClose={() => setSettingsDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Discord Integration Settings</DialogTitle>
        <DialogContent>
          <Typography variant="h6" gutterBottom>
            Notification Settings
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Choose which events should trigger Discord notifications.
          </Typography>
          
          {Object.entries(notificationSettings).map(([key, value]) => (
            <FormControlLabel
              key={key}
              control={
                <Switch
                  checked={value}
                  onChange={(e) => setNotificationSettings({
                    ...notificationSettings,
                    [key]: e.target.checked
                  })}
                />
              }
              label={key.split('_').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
              ).join(' ')}
              sx={{ display: 'block', mb: 1 }}
            />
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleUpdateNotificationSettings}
            variant="contained"
            disabled={loading}
          >
            Save Settings
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DiscordIntegration;