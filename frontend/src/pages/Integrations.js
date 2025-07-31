import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Alert
} from '@mui/material';
import GitHubIntegration from '../components/GitHubIntegration';
import SlackIntegration from '../components/SlackIntegration';
import DiscordIntegration from '../components/DiscordIntegration';
import GoogleCalendarIntegration from '../components/GoogleCalendarIntegration';
import api from '../services/api';

const Integrations = () => {
  const location = useLocation();

  useEffect(() => {
    // Handle OAuth callbacks
    const handleOAuthCallback = async () => {
      const urlParams = new URLSearchParams(location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const error = urlParams.get('error');

      if (error) {
        console.error('OAuth error:', error);
        return;
      }

      if (code && state) {
        try {
          if (location.pathname === '/integrations/github/callback') {
            await api.post('/api/integrations/github/connect/', {
              code: code,
              state: state
            });
          } else if (location.pathname === '/integrations/slack/callback') {
            await api.post('/api/integrations/slack/connect/', {
              code: code,
              state: state
            });
          } else if (location.pathname === '/integrations/discord/callback') {
            await api.post('/api/integrations/discord/connect/', {
              code: code,
              state: state
            });
          } else if (location.pathname === '/integrations/google/callback') {
            await api.post('/api/integrations/google-calendar/connect/', {
              code: code,
              state: state
            });
          }
          
          // Redirect to clean URL
          window.history.replaceState({}, document.title, '/integrations');
          
          // Refresh the page to show the connected integration
          window.location.reload();
        } catch (error) {
          console.error('Error connecting integration:', error);
        }
      }
    };

    if (location.pathname.includes('/callback')) {
      handleOAuthCallback();
    }
  }, [location]);

  return (
    <Container maxWidth="lg">
      <Box py={3}>
        <Typography variant="h4" component="h1" gutterBottom>
          Integrations
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Connect external services to enhance your project management workflow.
        </Typography>

        <Box mt={4}>
          <GitHubIntegration />
        </Box>

        <Box mt={4}>
          <SlackIntegration />
        </Box>

        <Box mt={4}>
          <DiscordIntegration />
        </Box>

        <Box mt={4}>
          <GoogleCalendarIntegration />
        </Box>

        {/* Future integrations can be added here */}
        <Box mt={4}>
          <Alert severity="info">
            More integrations coming soon: Jira, Trello, Microsoft Teams, and more!
          </Alert>
        </Box>
      </Box>
    </Container>
  );
};

export default Integrations;