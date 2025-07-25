import React from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent, Button, Chip } from '@mui/material';
import { Add, Folder } from '@mui/icons-material';

const Projects = () => {
  const mockProjects = [
    {
      id: 1,
      name: 'Project Alpha',
      description: 'Main development project',
      status: 'active',
      progress: 75
    },
    {
      id: 2,
      name: 'Project Beta',
      description: 'Client project',
      status: 'pending',
      progress: 45
    },
    {
      id: 3,
      name: 'Project Gamma',
      description: 'Internal tool',
      status: 'completed',
      progress: 100
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'pending': return 'warning';
      case 'completed': return 'primary';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Projects
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          sx={{ mb: 2 }}
        >
          New Project
        </Button>
      </Box>

      <Grid container spacing={3}>
        {mockProjects.map((project) => (
          <Grid item xs={12} md={6} lg={4} key={project.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Folder sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" component="div">
                    {project.name}
                  </Typography>
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {project.description}
                </Typography>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Chip 
                    label={project.status} 
                    color={getStatusColor(project.status)}
                    size="small"
                  />
                  <Typography variant="body2" color="text.secondary">
                    {project.progress}% complete
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default Projects;