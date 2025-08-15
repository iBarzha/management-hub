import React, { useEffect, useState } from 'react';
import {Box, Typography, Grid, Card, CardContent, Button, Chip, CircularProgress, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, FormControl, InputLabel, Select, MenuItem, Menu} from '@mui/material';
import { 
  Add, Folder, People, CalendarToday, 
  Assignment, FilterList, Visibility} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { fetchProjects, createProject } from '../store/slices/projectSlice';
import { fetchTeams } from '../store/slices/teamSlice';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

const Projects = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { projects, isLoading, error } = useSelector((state) => state.projects);
  const { teams } = useSelector((state) => state.teams);
  const [openDialog, setOpenDialog] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');
  
  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  useEffect(() => {
    dispatch(fetchProjects());
    dispatch(fetchTeams());
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

  const handleCreateProject = async (data) => {
    try {
      await dispatch(createProject({
        ...data,
        team_id: data.team_id ? parseInt(data.team_id) : null,
      })).unwrap();
      await dispatch(fetchProjects());
      setOpenDialog(false);
      reset();
    } catch (err) {
      console.error('Failed to create project:', err);
    }
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
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              Projects
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Manage and track all your projects in one place
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<FilterList />}
              sx={{ borderRadius: 2 }}
              onClick={(e) => {
                setAnchorEl(e.currentTarget);
                setSelectedProject('filter');
              }}
            >
              Filter
            </Button>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setOpenDialog(true)}
              sx={{ 
                borderRadius: 2,
                background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #1e40af 0%, #5b21b6 100%)',
                }
              }}
            >
              New Project
            </Button>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          {[{ label: 'All Projects', count: projects.length, active: true }, 
            { label: 'Active', count: projects.filter(p => p.status === 'active').length }, 
            { label: 'Planning', count: projects.filter(p => p.status === 'planning').length }, 
            { label: 'Completed', count: projects.filter(p => p.status === 'completed').length }].map((tab, index) => (
            <Chip
              key={index}
              label={`${tab.label} (${tab.count})`}
              clickable
              color={tab.active ? 'primary' : 'default'}
              variant={tab.active ? 'filled' : 'outlined'}
              sx={{ 
                borderRadius: 2,
                '&:hover': { backgroundColor: tab.active ? 'primary.main' : 'action.hover' }
              }}
            />
          ))}
        </Box>
      </Box>

      {projects.length === 0 ? (
        <Card sx={{ textAlign: 'center', py: 8 }}>
          <CardContent>
            <Folder sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
              No projects yet
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 400, mx: 'auto' }}>
              Projects help you organize tasks, collaborate with team members, and track progress towards your goals.
            </Typography>
            <Button 
              variant="contained" 
              size="large"
              startIcon={<Add />} 
              onClick={() => setOpenDialog(true)}
              sx={{ 
                borderRadius: 2,
                background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                px: 4, py: 1.5
              }}
            >
              Create Your First Project
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {projects.filter(project => filterStatus === 'all' || project.status === filterStatus).map((project) => (
            <Grid item xs={12} md={6} lg={4} key={project.id}>
              <Card 
                sx={{ 
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 8px 25px 0 rgb(0 0 0 / 0.15)',
                  }
                }}
                onClick={() => navigate(`/projects/${project.id}`)}
              >
                <CardContent sx={{ flexGrow: 1, p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Box
                        sx={{
                          width: 48,
                          height: 48,
                          borderRadius: 2.5,
                          background: `linear-gradient(135deg, ${getStatusColor(project.status) === 'success' ? '#10b981' : getStatusColor(project.status) === 'warning' ? '#f59e0b' : '#2563eb'}20 0%, ${getStatusColor(project.status) === 'success' ? '#10b981' : getStatusColor(project.status) === 'warning' ? '#f59e0b' : '#2563eb'}10 100%)`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: getStatusColor(project.status) === 'success' ? '#10b981' : getStatusColor(project.status) === 'warning' ? '#f59e0b' : '#2563eb'
                        }}
                      >
                        <Folder fontSize="medium" />
                      </Box>
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                          {project.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {project.team?.name || 'No team assigned'}
                        </Typography>
                      </Box>
                    </Box>
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={<Visibility />}
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/projects/${project.id}`);
                      }}
                      sx={{
                        borderRadius: 2,
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                          transform: 'translateY(-1px)',
                          boxShadow: '0 6px 20px rgba(102, 126, 234, 0.4)',
                        },
                        transition: 'all 0.2s ease-in-out'
                      }}
                    >
                      Details
                    </Button>
                  </Box>
                  
                  <Typography 
                    variant="body2" 
                    color="text.secondary" 
                    sx={{ 
                      mb: 3, 
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      minHeight: '2.5rem'
                    }}
                  >
                    {project.description || 'No description provided'}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    <Chip 
                      label={project.status.replace('_', ' ')} 
                      color={getStatusColor(project.status)}
                      size="small"
                      sx={{ 
                        fontWeight: 600,
                        textTransform: 'capitalize',
                        '& .MuiChip-label': { px: 1.5 }
                      }}
                    />
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <CalendarToday sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(project.start_date)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Assignment sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">
                        0 tasks
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <People sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">
                        {project.team?.member_count || 0}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Project Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleSubmit(handleCreateProject)} sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Project Name"
              margin="normal"
              {...register('name', { required: 'Name is required' })}
              error={!!errors.name}
              helperText={errors.name?.message}
            />
            
            <TextField
              fullWidth
              label="Description"
              margin="normal"
              multiline
              rows={3}
              {...register('description')}
            />
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Status</InputLabel>
              <Select
                {...register('status')}
                defaultValue="planning"
              >
                <MenuItem value="planning">Planning</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="on_hold">On Hold</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="archived">Archived</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth margin="normal">
              <InputLabel>Team</InputLabel>
              <Select
                {...register('team_id')}
                displayEmpty
              >
                <MenuItem value="">No Team</MenuItem>
                {teams.map((team) => (
                  <MenuItem key={team.id} value={team.id}>
                    {team.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <TextField
              fullWidth
              label="Start Date"
              type="date"
              margin="normal"
              InputLabelProps={{ shrink: true }}
              {...register('start_date')}
            />
            
            <TextField
              fullWidth
              label="End Date"
              type="date"
              margin="normal"
              InputLabelProps={{ shrink: true }}
              {...register('end_date')}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmit(handleCreateProject)} variant="contained">
            Create Project
          </Button>
        </DialogActions>
      </Dialog>

      
      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        {selectedProject === 'filter' ? (
          [{ label: 'All Projects', value: 'all' },
           { label: 'Active', value: 'active' },
           { label: 'Planning', value: 'planning' },
           { label: 'On Hold', value: 'on_hold' },
           { label: 'Completed', value: 'completed' },
           { label: 'Archived', value: 'archived' }].map((filter) => (
            <MenuItem key={filter.value} onClick={() => {
              setFilterStatus(filter.value);
              setAnchorEl(null);
            }}>
              {filter.label}
            </MenuItem>
          ))
        ) : (
          [
            <MenuItem key="view" onClick={() => {
              navigate(`/projects/${selectedProject?.id}`);
              setAnchorEl(null);
            }}>View Details</MenuItem>,
            <MenuItem key="edit" onClick={() => {
              console.log('Edit project:', selectedProject?.name);
              setAnchorEl(null);
            }}>Edit Project</MenuItem>,
            <MenuItem key="tasks" onClick={() => {
              navigate(`/tasks?project=${selectedProject?.id}`);
              setAnchorEl(null);
            }}>View Tasks</MenuItem>,
            <MenuItem key="archive" onClick={() => {
              console.log('Archive project:', selectedProject?.name);
              setAnchorEl(null);
            }}>Archive</MenuItem>
          ]
        )}
      </Menu>
    </Box>
  );
};

export default Projects;