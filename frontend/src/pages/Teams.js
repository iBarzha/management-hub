import React from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent, Button, Avatar, Chip } from '@mui/material';
import { Add, People } from '@mui/icons-material';

const Teams = () => {
  const mockTeams = [
    {
      id: 1,
      name: 'Development Team',
      description: 'Frontend and backend developers',
      memberCount: 5,
      status: 'active'
    },
    {
      id: 2,
      name: 'Design Team',
      description: 'UI/UX designers and creative team',
      memberCount: 3,
      status: 'active'
    },
    {
      id: 3,
      name: 'QA Team',
      description: 'Quality assurance and testing',
      memberCount: 2,
      status: 'active'
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Teams
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          sx={{ mb: 2 }}
        >
          New Team
        </Button>
      </Box>

      <Grid container spacing={3}>
        {mockTeams.map((team) => (
          <Grid item xs={12} md={6} lg={4} key={team.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                    <People />
                  </Avatar>
                  <Box>
                    <Typography variant="h6" component="div">
                      {team.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {team.memberCount} members
                    </Typography>
                  </Box>
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {team.description}
                </Typography>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Chip 
                    label={team.status} 
                    color={getStatusColor(team.status)}
                    size="small"
                  />
                  <Button size="small" variant="outlined">
                    View Details
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default Teams;