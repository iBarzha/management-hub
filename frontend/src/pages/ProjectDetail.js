import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, Chip,
  Tab, Tabs, Grid, LinearProgress, IconButton, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, FormControl,
  InputLabel, Select, MenuItem as SelectMenuItem
} from '@mui/material';
import {
  ArrowBack, Edit, Delete, People, Assignment,
  CalendarToday, Folder, Add, CheckCircle, Schedule, Archive, Restore
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { fetchProjects, updateProject, deleteProject } from '../store/slices/projectSlice';
import { fetchTasks } from '../store/slices/taskSlice';
import { fetchTeams } from '../store/slices/teamSlice';
import { useForm } from 'react-hook-form';

const ProjectDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { projects } = useSelector((state) => state.projects);
  const { tasks } = useSelector((state) => state.tasks);
  const { teams } = useSelector((state) => state.teams);
  
  const [tabValue, setTabValue] = useState(0);
  const [editDialog, setEditDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);
  
  const { register, handleSubmit, setValue, formState: { errors } } = useForm();
  
  const project = projects.find(p => p.id === parseInt(id));
  const projectTasks = tasks.filter(task => task.project?.id === parseInt(id));
  const completedTasks = projectTasks.filter(task => task.status === 'done');
  const progress = projectTasks.length > 0 ? Math.round((completedTasks.length / projectTasks.length) * 100) : 0;

  useEffect(() => {
    dispatch(fetchProjects());
    dispatch(fetchTasks());
    dispatch(fetchTeams());
  }, [dispatch]);

  useEffect(() => {
    if (project) {
      setValue('name', project.name);
      setValue('description', project.description);
      setValue('status', project.status);
      setValue('team_id', project.team?.id || '');
      setValue('start_date', project.start_date);
      setValue('end_date', project.end_date);
    }
  }, [project, setValue]);

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
    return dateString ? new Date(dateString).toLocaleDateString() : 'Not set';
  };

  const handleUpdateProject = async (data) => {
    try {
      await dispatch(updateProject({
        id: project.id,
        ...data,
        team_id: data.team_id ? parseInt(data.team_id) : null,
      })).unwrap();
      await dispatch(fetchProjects());
      setEditDialog(false);
    } catch (err) {
      console.error('Failed to update project:', err);
    }
  };

  const handleDeleteProject = async () => {
    try {
      await dispatch(deleteProject(project.id)).unwrap();
      setDeleteDialog(false);
      navigate('/projects');
    } catch (err) {
      console.error('Failed to delete project:', err);
    }
  };

  const handleArchiveProject = async () => {
    try {
      await dispatch(updateProject({
        id: project.id,
        status: project.status === 'archived' ? 'active' : 'archived'
      })).unwrap();
      await dispatch(fetchProjects());
    } catch (err) {
      console.error('Failed to archive/restore project:', err);
    }
  };

  if (!project) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" color="error">
          Project not found
        </Typography>
        <Button onClick={() => navigate('/projects')} sx={{ mt: 2 }}>
          Back to Projects
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <IconButton onClick={() => navigate('/projects')} sx={{ mr: 1 }}>
            <ArrowBack />
          </IconButton>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              {project.name}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {project.description || 'No description provided'}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<Edit />}
              onClick={() => setEditDialog(true)}
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
              Edit
            </Button>
            <Button
              variant="contained"
              startIcon={project.status === 'archived' ? <Restore /> : <Archive />}
              onClick={handleArchiveProject}
              sx={{
                borderRadius: 2,
                background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                boxShadow: '0 4px 15px rgba(240, 147, 251, 0.3)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #e084ec 0%, #e6495d 100%)',
                  transform: 'translateY(-1px)',
                  boxShadow: '0 6px 20px rgba(240, 147, 251, 0.4)',
                },
                transition: 'all 0.2s ease-in-out'
              }}
            >
              {project.status === 'archived' ? 'Restore' : 'Archive'}
            </Button>
            <Button
              variant="contained"
              startIcon={<Delete />}
              onClick={() => setDeleteDialog(true)}
              sx={{
                borderRadius: 2,
                background: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)',
                boxShadow: '0 4px 15px rgba(255, 107, 107, 0.3)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #ff5757 0%, #dc4c64 100%)',
                  transform: 'translateY(-1px)',
                  boxShadow: '0 6px 20px rgba(255, 107, 107, 0.4)',
                },
                transition: 'all 0.2s ease-in-out'
              }}
            >
              Delete
            </Button>
          </Box>
        </Box>

        {/* Project Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Assignment sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {projectTasks.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Tasks
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <CheckCircle sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {completedTasks.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Completed
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <People sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {project.team?.member_count || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Team Members
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Schedule sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {progress}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Progress
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Project Info Card */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Status
                  </Typography>
                  <Chip 
                    label={project.status.replace('_', ' ')} 
                    color={getStatusColor(project.status)}
                    sx={{ textTransform: 'capitalize', fontWeight: 600 }}
                  />
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Team
                  </Typography>
                  <Typography variant="body1">
                    {project.team?.name || 'No team assigned'}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Start Date
                  </Typography>
                  <Typography variant="body1">
                    {formatDate(project.start_date)}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    End Date
                  </Typography>
                  <Typography variant="body1">
                    {formatDate(project.end_date)}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
            
            {/* Progress Bar */}
            <Box sx={{ mt: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Overall Progress
                </Typography>
                <Typography variant="subtitle2" color="text.secondary">
                  {completedTasks.length}/{projectTasks.length} tasks completed
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{ 
                  height: 10, 
                  borderRadius: 5,
                  backgroundColor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 5,
                    background: progress >= 80 ? 'linear-gradient(90deg, #10b981, #059669)' : 
                               progress >= 50 ? 'linear-gradient(90deg, #f59e0b, #d97706)' : 
                               'linear-gradient(90deg, #2563eb, #1e40af)'
                  }
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab label="Tasks" />
            <Tab label="Activity" />
            <Tab label="Files" />
          </Tabs>
        </Box>
        
        <CardContent>
          {tabValue === 0 && (
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6">Project Tasks</Typography>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => navigate(`/tasks?project=${project.id}`)}
                >
                  Add Task
                </Button>
              </Box>
              
              {projectTasks.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Assignment sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No tasks yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Create tasks to start tracking progress for this project
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => navigate(`/tasks?project=${project.id}`)}
                  >
                    Create First Task
                  </Button>
                </Box>
              ) : (
                <Grid container spacing={2}>
                  {projectTasks.map((task) => (
                    <Grid item xs={12} key={task.id}>
                      <Card variant="outlined">
                        <CardContent sx={{ py: 2 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box>
                              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                                {task.title}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {task.description || 'No description'}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Chip 
                                label={task.status} 
                                size="small"
                                color={task.status === 'done' ? 'success' : 
                                       task.status === 'in_progress' ? 'warning' : 'default'}
                              />
                              <Chip 
                                label={task.priority} 
                                size="small"
                                color={task.priority === 'high' ? 'error' : 
                                       task.priority === 'medium' ? 'warning' : 'success'}
                              />
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </Box>
          )}
          
          {tabValue === 1 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <CalendarToday sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Activity feed coming soon
              </Typography>
            </Box>
          )}
          
          {tabValue === 2 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Folder sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                File management coming soon
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialog}
        onClose={() => setDeleteDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Delete color="error" />
            <Typography variant="h6">
              Delete Project
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            Are you sure you want to delete <strong>{project.name}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This action cannot be undone. All tasks, files, and data associated with this project will be permanently removed.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteProject} 
            color="error" 
            variant="contained"
            startIcon={<Delete />}
          >
            Delete Project
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Project</DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleSubmit(handleUpdateProject)} sx={{ mt: 2 }}>
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
                defaultValue={project.status}
              >
                <SelectMenuItem value="planning">Planning</SelectMenuItem>
                <SelectMenuItem value="active">Active</SelectMenuItem>
                <SelectMenuItem value="on_hold">On Hold</SelectMenuItem>
                <SelectMenuItem value="completed">Completed</SelectMenuItem>
                <SelectMenuItem value="archived">Archived</SelectMenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth margin="normal">
              <InputLabel>Team</InputLabel>
              <Select
                {...register('team_id')}
                displayEmpty
                defaultValue={project.team?.id || ''}
              >
                <SelectMenuItem value="">No Team</SelectMenuItem>
                {teams.map((team) => (
                  <SelectMenuItem key={team.id} value={team.id}>
                    {team.name}
                  </SelectMenuItem>
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
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmit(handleUpdateProject)} variant="contained">
            Update Project
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProjectDetail;