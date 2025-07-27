import React, { useEffect } from 'react';
import { Box, Typography, Grid, Card, CardContent, Button, Chip, CircularProgress } from '@mui/material';
import { Add, Folder } from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { fetchProjects } from '../store/slices/projectSlice';

const Projects = () => {
  const dispatch = useDispatch();
  const { projects, isLoading, error } = useSelector((state) => state.projects);

  useEffect(() => {
    dispatch(fetchProjects());
  }, [dispatch]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'planning': return 'info';
      case 'on_hold': return 'warning';
      case 'completed': return 'primary';
      case 'archived': return 'default';
      default: return 'default';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography color="error" variant="h6">
          Error loading projects: {error}
        </Typography>
      </Box>
    );
  }

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

      {projects.length === 0 ? (
        <Box textAlign="center" py={8}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No projects found
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Create your first project to get started
          </Typography>
          <Button variant="contained" startIcon={<Add />}>
            Create Project
          </Button>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project) => (
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
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Chip 
                      label={project.status} 
                      color={getStatusColor(project.status)}
                      size="small"
                    />
                    <Typography variant="body2" color="text.secondary">
                      {project.team?.name}
                    </Typography>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary">
                    {formatDate(project.start_date)} - {formatDate(project.end_date)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default Projects;