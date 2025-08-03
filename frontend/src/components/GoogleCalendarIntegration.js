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
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Event as CalendarIcon,
  Sync as SyncIcon,
  Link as LinkIcon,
  LinkOff as UnlinkIcon,
  OpenInNew as OpenInNewIcon,
  VideoCall as VideoCallIcon,
  Schedule as ScheduleIcon,
  People as PeopleIcon
} from '@mui/icons-material';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { useSelector } from 'react-redux';
import api from '../services/api';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`calendar-tabpanel-${index}`}
      aria-labelledby={`calendar-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const GoogleCalendarIntegration = () => {
  const { user } = useSelector((state) => state.auth);
  const [integration, setIntegration] = useState(null);
  const [events, setEvents] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [calendars, setCalendars] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [createEventDialogOpen, setCreateEventDialogOpen] = useState(false);
  const [createMeetingDialogOpen, setCreateMeetingDialogOpen] = useState(false);
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    start_datetime: new Date(),
    end_datetime: new Date(Date.now() + 60 * 60 * 1000), // 1 hour from now
    location: '',
    attendees: [],
    timezone: 'UTC'
  });
  const [newMeeting, setNewMeeting] = useState({
    title: '',
    description: '',
    start_datetime: new Date(),
    end_datetime: new Date(Date.now() + 60 * 60 * 1000),
    location: '',
    project: null,
    attendees: [],
    create_calendar_event: true
  });

  useEffect(() => {
    loadIntegration();
    loadProjects();
  }, []);

  const loadIntegration = async () => {
    try {
      const response = await api.get('/integrations/google-calendar/');
      if (response.data.length > 0) {
        setIntegration(response.data[0]);
        loadCalendars();
        loadEvents();
        loadMeetings();
      }
    } catch (error) {
      console.error('Error loading Google Calendar integration:', error);
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

  const loadCalendars = async () => {
    try {
      const response = await api.get(`/integrations/google-calendar/${integration.id}/calendars/`);
      setCalendars(response.data.calendars || []);
    } catch (error) {
      console.error('Error loading calendars:', error);
    }
  };

  const loadEvents = async () => {
    try {
      const response = await api.get('/integrations/calendar-events/');
      setEvents(response.data);
    } catch (error) {
      console.error('Error loading events:', error);
    }
  };

  const loadMeetings = async () => {
    try {
      const response = await api.get('/integrations/meeting-schedules/');
      setMeetings(response.data);
    } catch (error) {
      console.error('Error loading meetings:', error);
    }
  };

  const handleConnect = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Get authorization URL
      const authResponse = await api.get('/integrations/google-calendar/auth-url/');
      
      // Redirect to Google OAuth
      window.location.href = authResponse.data.auth_url;
    } catch (error) {
      setError('Failed to initiate Google Calendar connection');
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      setError('');
      
      await api.delete(`/api/integrations/google-calendar/${integration.id}/disconnect/`);
      
      setIntegration(null);
      setEvents([]);
      setMeetings([]);
      setCalendars([]);
      setSuccess('Google Calendar integration disconnected successfully');
      setLoading(false);
    } catch (error) {
      setError('Failed to disconnect Google Calendar integration');
      setLoading(false);
    }
  };

  const handleSyncEvents = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await api.post(`/api/integrations/google-calendar/${integration.id}/sync-events/`);
      loadEvents();
      setSuccess(`Synced ${response.data.events_synced} events`);
      setLoading(false);
    } catch (error) {
      setError('Failed to sync events');
      setLoading(false);
    }
  };

  const handleCreateEvent = async () => {
    try {
      setLoading(true);
      setError('');
      
      const eventData = {
        ...newEvent,
        start_datetime: newEvent.start_datetime.toISOString(),
        end_datetime: newEvent.end_datetime.toISOString(),
        attendees: newEvent.attendees.map(attendee => attendee.email || attendee)
      };
      
      await api.post('/integrations/calendar-events/create-from-google/', eventData);
      
      loadEvents();
      setCreateEventDialogOpen(false);
      setNewEvent({
        title: '',
        description: '',
        start_datetime: new Date(),
        end_datetime: new Date(Date.now() + 60 * 60 * 1000),
        location: '',
        attendees: [],
        timezone: 'UTC'
      });
      setSuccess('Event created successfully');
      setLoading(false);
    } catch (error) {
      setError('Failed to create event');
      setLoading(false);
    }
  };

  const handleCreateMeeting = async () => {
    try {
      setLoading(true);
      setError('');
      
      const meetingData = {
        ...newMeeting,
        start_datetime: newMeeting.start_datetime.toISOString(),
        end_datetime: newMeeting.end_datetime.toISOString(),
        project: newMeeting.project?.id,
        attendees: newMeeting.attendees.map(attendee => attendee.id || attendee)
      };
      
      await api.post('/integrations/meeting-schedules/', meetingData);
      
      loadMeetings();
      setCreateMeetingDialogOpen(false);
      setNewMeeting({
        title: '',
        description: '',
        start_datetime: new Date(),
        end_datetime: new Date(Date.now() + 60 * 60 * 1000),
        location: '',
        project: null,
        attendees: [],
        create_calendar_event: true
      });
      setSuccess('Meeting scheduled successfully');
      setLoading(false);
    } catch (error) {
      setError('Failed to create meeting');
      setLoading(false);
    }
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (!integration) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <CalendarIcon sx={{ mr: 2, fontSize: 40, color: '#4285f4' }} />
            <Typography variant="h5">Google Calendar Integration</Typography>
          </Box>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Typography variant="body1" color="text.secondary" paragraph>
            Connect your Google Calendar to schedule meetings, sync events, and manage your calendar from within your project management hub.
          </Typography>
          
          <Button
            variant="contained"
            startIcon={<CalendarIcon />}
            onClick={handleConnect}
            disabled={loading}
            sx={{ backgroundColor: '#4285f4', '&:hover': { backgroundColor: '#3367d6' } }}
          >
            {loading ? <CircularProgress size={20} /> : 'Connect Google Calendar'}
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
              <Avatar sx={{ mr: 2, backgroundColor: '#4285f4' }}>
                <CalendarIcon />
              </Avatar>
              <Box>
                <Typography variant="h6">Google Calendar</Typography>
                <Typography variant="body2" color="text.secondary">
                  {integration.google_user_email}
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
                <Typography variant="h6">{events.length}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Events
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box textAlign="center">
                <Typography variant="h6">{meetings.length}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Meetings
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box textAlign="center">
                <Typography variant="h6">{calendars.length}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Calendars
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
            <Tab label="Events" />
            <Tab label="Meetings" />
            <Tab label="Calendars" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Calendar Events</Typography>
            <Box>
              <Button
                variant="outlined"
                startIcon={<SyncIcon />}
                onClick={handleSyncEvents}
                disabled={loading}
                sx={{ mr: 1 }}
              >
                Sync Events
              </Button>
              <Button
                variant="contained"
                startIcon={<CalendarIcon />}
                onClick={() => setCreateEventDialogOpen(true)}
              >
                Create Event
              </Button>
            </Box>
          </Box>

          <List>
            {events.slice(0, 20).map((event) => (
              <ListItem key={event.id}>
                <ListItemAvatar>
                  <Avatar>
                    <CalendarIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={event.title}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {formatDateTime(event.start_datetime)} - {formatDateTime(event.end_datetime)}
                      </Typography>
                      {event.location && (
                        <Typography variant="body2" color="text.secondary">
                          📍 {event.location}
                        </Typography>
                      )}
                      <Box display="flex" alignItems="center" gap={1} mt={1}>
                        <Chip
                          label={event.status}
                          size="small"
                          color={event.status === 'confirmed' ? 'success' : 'default'}
                        />
                        {event.all_day && <Chip label="All Day" size="small" />}
                        {event.recurring && <Chip label="Recurring" size="small" />}
                      </Box>
                    </Box>
                  }
                />
                <Box>
                  {event.meeting_url && (
                    <IconButton
                      onClick={() => window.open(event.meeting_url, '_blank')}
                      title="Join Meeting"
                    >
                      <VideoCallIcon />
                    </IconButton>
                  )}
                </Box>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Meeting Schedules</Typography>
            <Button
              variant="contained"
              startIcon={<ScheduleIcon />}
              onClick={() => setCreateMeetingDialogOpen(true)}
            >
              Schedule Meeting
            </Button>
          </Box>

          <List>
            {meetings.map((meeting) => (
              <ListItem key={meeting.id}>
                <ListItemAvatar>
                  <Avatar>
                    <PeopleIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={meeting.title}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {formatDateTime(meeting.start_datetime)} - {formatDateTime(meeting.end_datetime)}
                      </Typography>
                      {meeting.location && (
                        <Typography variant="body2" color="text.secondary">
                          📍 {meeting.location}
                        </Typography>
                      )}
                      <Box display="flex" alignItems="center" gap={1} mt={1}>
                        <Chip
                          label={meeting.status}
                          size="small"
                          color={meeting.status === 'scheduled' ? 'primary' : 'default'}
                        />
                        <Chip label={`${meeting.attendees_list?.length || 0} attendees`} size="small" />
                      </Box>
                    </Box>
                  }
                />
                <Box>
                  {meeting.meeting_url && (
                    <IconButton
                      onClick={() => window.open(meeting.meeting_url, '_blank')}
                      title="Join Meeting"
                    >
                      <VideoCallIcon />
                    </IconButton>
                  )}
                </Box>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" mb={2}>Available Calendars</Typography>
          <List>
            {calendars.map((calendar, index) => (
              <ListItem key={index}>
                <ListItemAvatar>
                  <Avatar sx={{ backgroundColor: calendar.backgroundColor || '#4285f4' }}>
                    <CalendarIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={calendar.summary}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {calendar.description}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1} mt={1}>
                        {calendar.primary && <Chip label="Primary" size="small" color="primary" />}
                        <Chip label={calendar.accessRole} size="small" />
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </TabPanel>
      </Card>

      {/* Create Event Dialog */}
      <Dialog open={createEventDialogOpen} onClose={() => setCreateEventDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Calendar Event</DialogTitle>
        <DialogContent>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Event Title"
                  value={newEvent.title}
                  onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Description"
                  value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                />
              </Grid>
              <Grid item xs={6}>
                <DateTimePicker
                  label="Start Date & Time"
                  value={newEvent.start_datetime}
                  onChange={(newValue) => setNewEvent({ ...newEvent, start_datetime: newValue })}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={6}>
                <DateTimePicker
                  label="End Date & Time"
                  value={newEvent.end_datetime}
                  onChange={(newValue) => setNewEvent({ ...newEvent, end_datetime: newValue })}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Location"
                  value={newEvent.location}
                  onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
                />
              </Grid>
            </Grid>
          </LocalizationProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateEventDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateEvent}
            variant="contained"
            disabled={!newEvent.title || loading}
          >
            Create Event
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Meeting Dialog */}
      <Dialog open={createMeetingDialogOpen} onClose={() => setCreateMeetingDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Schedule Meeting</DialogTitle>
        <DialogContent>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Meeting Title"
                  value={newMeeting.title}
                  onChange={(e) => setNewMeeting({ ...newMeeting, title: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  options={projects}
                  getOptionLabel={(option) => option.name}
                  value={newMeeting.project}
                  onChange={(event, newValue) => setNewMeeting({ ...newMeeting, project: newValue })}
                  renderInput={(params) => (
                    <TextField {...params} label="Project" fullWidth />
                  )}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Description"
                  value={newMeeting.description}
                  onChange={(e) => setNewMeeting({ ...newMeeting, description: e.target.value })}
                />
              </Grid>
              <Grid item xs={6}>
                <DateTimePicker
                  label="Start Date & Time"
                  value={newMeeting.start_datetime}
                  onChange={(newValue) => setNewMeeting({ ...newMeeting, start_datetime: newValue })}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={6}>
                <DateTimePicker
                  label="End Date & Time"
                  value={newMeeting.end_datetime}
                  onChange={(newValue) => setNewMeeting({ ...newMeeting, end_datetime: newValue })}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Location"
                  value={newMeeting.location}
                  onChange={(e) => setNewMeeting({ ...newMeeting, location: e.target.value })}
                />
              </Grid>
            </Grid>
          </LocalizationProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateMeetingDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateMeeting}
            variant="contained"
            disabled={!newMeeting.title || !newMeeting.project || loading}
          >
            Schedule Meeting
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GoogleCalendarIntegration;