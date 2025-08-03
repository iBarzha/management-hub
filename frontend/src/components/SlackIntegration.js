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
  Alert,
  CircularProgress,
  Tab,
  Tabs,
  FormControlLabel,
  Switch
} from '@mui/material';
import {
  Chat as SlackIcon,
  Sync as SyncIcon,
  LinkOff as UnlinkIcon,
  Send as SendIcon,
  Tag as TagIcon,
  Notifications as NotificationsIcon,
  NotificationsOff as NotificationsOffIcon
} from '@mui/icons-material';
import api from '../services/api';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`slack-tabpanel-${index}`}
      aria-labelledby={`slack-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const SlackIntegration = () => {
  const [integration, setIntegration] = useState(null);
  const [channels, setChannels] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [messageDialogOpen, setMessageDialogOpen] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [messageText, setMessageText] = useState('');

  useEffect(() => {
    loadIntegration();
  }, []);

  const loadIntegration = async () => {
    try {
      const response = await api.get('/integrations/slack/');
      if (response.data.length > 0) {
        setIntegration(response.data[0]);
        loadChannels();
        loadMessages();
      }
    } catch (error) {
      console.error('Error loading Slack integration:', error);
    }
  };

  const loadChannels = async () => {
    try {
      const response = await api.get('/integrations/slack-channels/');
      setChannels(response.data);
    } catch (error) {
      console.error('Error loading channels:', error);
    }
  };

  const loadMessages = async () => {
    try {
      const response = await api.get('/integrations/slack-messages/');
      setMessages(response.data);
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const handleConnect = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Get authorization URL
      const authResponse = await api.get('/integrations/slack/auth-url/');
      
      // Redirect to Slack OAuth
      window.location.href = authResponse.data.auth_url;
    } catch (error) {
      setError('Failed to initiate Slack connection');
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      setError('');
      
      await api.delete(`/api/integrations/slack/${integration.id}/disconnect/`);
      
      setIntegration(null);
      setChannels([]);
      setMessages([]);
      setSuccess('Slack integration disconnected successfully');
      setLoading(false);
    } catch (error) {
      setError('Failed to disconnect Slack integration');
      setLoading(false);
    }
  };

  const handleSyncChannels = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await api.post('/integrations/slack-channels/sync/');
      setChannels(response.data.channels);
      setSuccess(`Synced ${response.data.synced_count} channels`);
      setLoading(false);
    } catch (error) {
      setError('Failed to sync channels');
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await api.post(
        `/api/integrations/slack-channels/${selectedChannel.id}/send-message/`,
        { text: messageText }
      );
      
      loadMessages();
      setMessageDialogOpen(false);
      setSelectedChannel(null);
      setMessageText('');
      setSuccess('Message sent successfully');
      setLoading(false);
    } catch (error) {
      setError('Failed to send message');
      setLoading(false);
    }
  };

  const handleToggleNotifications = async (channel, enabled) => {
    try {
      await api.patch(`/api/integrations/slack-channels/${channel.id}/`, {
        notifications_enabled: enabled
      });
      
      loadChannels();
      setSuccess(`Notifications ${enabled ? 'enabled' : 'disabled'} for #${channel.channel_name}`);
    } catch (error) {
      setError('Failed to update notification settings');
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
            <SlackIcon sx={{ mr: 2, fontSize: 40, color: '#4A154B' }} />
            <Typography variant="h5">Slack Integration</Typography>
          </Box>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Typography variant="body1" color="text.secondary" paragraph>
            Connect your Slack workspace to receive notifications about project updates, 
            task assignments, and use slash commands to manage your projects.
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>Features:</Typography>
            <ul>
              <li>Automatic project notifications in Slack channels</li>
              <li>Slash commands: /tasks, /create-task, /project-status</li>
              <li>Channel-specific notification settings</li>
              <li>Rich message formatting with attachments</li>
            </ul>
          </Box>
          
          <Button
            variant="contained"
            startIcon={<SlackIcon />}
            onClick={handleConnect}
            disabled={loading}
            sx={{ backgroundColor: '#4A154B', '&:hover': { backgroundColor: '#350d36' } }}
          >
            {loading ? <CircularProgress size={20} /> : 'Connect Slack'}
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
              <Avatar sx={{ mr: 2, backgroundColor: '#4A154B' }}>
                <SlackIcon />
              </Avatar>
              <Box>
                <Typography variant="h6">{integration.team_name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Slack Workspace
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
            <Grid item xs={6}>
              <Box textAlign="center">
                <Typography variant="h6">{channels.length}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Channels
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box textAlign="center">
                <Typography variant="h6">{messages.length}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Messages Sent
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
            <Tab label="Messages" />
            <Tab label="Slash Commands" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Channels</Typography>
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
                    <TagIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={`#${channel.channel_name}`}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {channel.is_private ? 'Private Channel' : 'Public Channel'}
                        {channel.is_archived && ' • Archived'}
                      </Typography>
                      {channel.project && (
                        <Chip 
                          label={`Connected to: ${channel.project.name}`} 
                          size="small" 
                          sx={{ mt: 1 }}
                        />
                      )}
                    </Box>
                  }
                />
                <Box>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={channel.notifications_enabled}
                        onChange={(e) => handleToggleNotifications(channel, e.target.checked)}
                        icon={<NotificationsOffIcon />}
                        checkedIcon={<NotificationsIcon />}
                      />
                    }
                    label=""
                  />
                  <IconButton
                    onClick={() => {
                      setSelectedChannel(channel);
                      setMessageDialogOpen(true);
                    }}
                    title="Send Message"
                  >
                    <SendIcon />
                  </IconButton>
                </Box>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>Recent Messages</Typography>
          
          <List>
            {messages.slice(0, 20).map((message) => (
              <ListItem key={message.id}>
                <ListItemText
                  primary={message.text.substring(0, 100) + (message.text.length > 100 ? '...' : '')}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Sent to #{message.channel?.channel_name} • {formatDate(message.created_at)}
                      </Typography>
                      <Chip
                        label={message.sent_successfully ? 'Delivered' : 'Failed'}
                        size="small"
                        color={message.sent_successfully ? 'success' : 'error'}
                        sx={{ mt: 1 }}
                      />
                      {message.error_message && (
                        <Typography variant="caption" color="error" display="block">
                          Error: {message.error_message}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>Available Slash Commands</Typography>
          
          <Box sx={{ mb: 3 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              To set up slash commands, create them in your Slack app settings and point them to: 
              <code>{window.location.origin}/api/integrations/slack/slash-command/</code>
            </Alert>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>/tasks</Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    List tasks from your projects. You can filter by status.
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Usage: /tasks [status]
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>/create-task</Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Create a new task quickly from Slack.
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Usage: /create-task &lt;title&gt;
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>/project-status</Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Get an overview of project progress and statistics.
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Usage: /project-status [project-name]
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>

      {/* Send Message Dialog */}
      <Dialog open={messageDialogOpen} onClose={() => setMessageDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Send Message to #{selectedChannel?.channel_name}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Message"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={messageText}
            onChange={(e) => setMessageText(e.target.value)}
            placeholder="Type your message here..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMessageDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSendMessage}
            variant="contained"
            disabled={!messageText.trim() || loading}
            startIcon={<SendIcon />}
          >
            Send Message
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SlackIntegration;