import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Switch,
  FormControlLabel,
  FormGroup,
  Divider,
  Button,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  CardHeader
} from '@mui/material';
import {
  Email as EmailIcon,
  Notifications as NotificationsIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { toast } from 'react-toastify';
import api from '../services/api';

const Settings = () => {
  const [preferences, setPreferences] = useState({
    email_notifications: {
      enabled: true,
      task_assignments: true,
      task_updates: false,
      project_updates: true,
      deadline_reminders: true,
      mentions: true,
      comments: false,
      other: false
    }
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const { user } = useSelector(state => state.auth);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const response = await api.get('/users/preferences/');
      setPreferences(response.data);
      setError('');
    } catch (error) {
      console.error('Error loading preferences:', error);
      setError('Failed to load preferences. Using defaults.');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailNotificationChange = (key) => (event) => {
    setPreferences(prev => ({
      ...prev,
      email_notifications: {
        ...prev.email_notifications,
        [key]: event.target.checked
      }
    }));
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      await api.patch('/users/preferences/', {
        notification_preferences: {
          email_notifications: preferences.email_notifications
        }
      });
      
      toast.success('Preferences saved successfully!', {
        position: "top-right",
        autoClose: 3000,
      });
      setError('');
    } catch (error) {
      console.error('Error saving preferences:', error);
      setError('Failed to save preferences. Please try again.');
      toast.error('Failed to save preferences', {
        position: "top-right",
        autoClose: 3000,
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <NotificationsIcon color="primary" />
          Notification Settings
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Configure how you want to receive notifications from the Project Management Hub.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mt: 4 }}>
          <Card sx={{ mb: 3 }}>
            <CardHeader
              avatar={<EmailIcon color="primary" />}
              title="Email Notifications"
              subheader="Configure which notifications you want to receive via email"
            />
            <CardContent>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.email_notifications?.enabled || false}
                      onChange={handleEmailNotificationChange('enabled')}
                      color="primary"
                    />
                  }
                  label="Enable Email Notifications"
                  sx={{ mb: 2, fontWeight: 'bold' }}
                />
                
                <Divider sx={{ my: 2 }} />
                
                <Box sx={{ ml: 4 }}>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2 }}>
                    Notification Types:
                  </Typography>
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={preferences.email_notifications?.task_assignments || false}
                        onChange={handleEmailNotificationChange('task_assignments')}
                        disabled={!preferences.email_notifications?.enabled}
                        color="primary"
                      />
                    }
                    label="Task Assignments"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={preferences.email_notifications?.task_updates || false}
                        onChange={handleEmailNotificationChange('task_updates')}
                        disabled={!preferences.email_notifications?.enabled}
                        color="primary"
                      />
                    }
                    label="Task Updates"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={preferences.email_notifications?.project_updates || false}
                        onChange={handleEmailNotificationChange('project_updates')}
                        disabled={!preferences.email_notifications?.enabled}
                        color="primary"
                      />
                    }
                    label="Project Updates"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={preferences.email_notifications?.deadline_reminders || false}
                        onChange={handleEmailNotificationChange('deadline_reminders')}
                        disabled={!preferences.email_notifications?.enabled}
                        color="primary"
                      />
                    }
                    label="Deadline Reminders"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={preferences.email_notifications?.mentions || false}
                        onChange={handleEmailNotificationChange('mentions')}
                        disabled={!preferences.email_notifications?.enabled}
                        color="primary"
                      />
                    }
                    label="Mentions"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={preferences.email_notifications?.comments || false}
                        onChange={handleEmailNotificationChange('comments')}
                        disabled={!preferences.email_notifications?.enabled}
                        color="primary"
                      />
                    }
                    label="Comments"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={preferences.email_notifications?.other || false}
                        onChange={handleEmailNotificationChange('other')}
                        disabled={!preferences.email_notifications?.enabled}
                        color="primary"
                      />
                    }
                    label="Other Notifications"
                  />
                </Box>
              </FormGroup>
              
              <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="body2" color="info.contrastText">
                  <strong>Note:</strong> Email notifications require EmailJS configuration. 
                  Make sure your administrator has set up the email service properly.
                  You'll receive emails at: <strong>{user?.email}</strong>
                </Typography>
              </Box>
            </CardContent>
          </Card>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button
              variant="outlined"
              onClick={loadPreferences}
              disabled={saving}
            >
              Reset
            </Button>
            <Button
              variant="contained"
              startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
              onClick={savePreferences}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Preferences'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default Settings;