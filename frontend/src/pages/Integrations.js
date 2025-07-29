import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Alert
} from '@mui/material';
import GitHubIntegration from '../components/GitHubIntegration';
import api from '../services/api';

const Integrations = () => {
  const location = useLocation();

  useEffect(() => {
    // Handle GitHub OAuth callback
    const handleGitHubCallback = async () => {
      const urlParams = new URLSearchParams(location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const error = urlParams.get('error');

      if (error) {
        console.error('GitHub OAuth error:', error);
        return;
      }

      if (code && state) {
        try {
          await api.post('/api/integrations/github/connect/', {
            code: code,
            state: state
          });
          
          // Redirect to clean URL
          window.history.replaceState({}, document.title, '/integrations');
          
          // Refresh the page to show the connected integration
          window.location.reload();
        } catch (error) {
          console.error('Error connecting GitHub:', error);
        }
      }
    };

    if (location.pathname === '/integrations/github/callback') {
      handleGitHubCallback();
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

        {/* Future integrations can be added here */}
        <Box mt={4}>
          <Alert severity="info">
            More integrations coming soon: Slack, Discord, Jira, and more!
          </Alert>
        </Box>
      </Box>
    </Container>
  );
};

export default Integrations;