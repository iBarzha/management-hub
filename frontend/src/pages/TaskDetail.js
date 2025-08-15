import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, Chip, 
  Grid, IconButton, Dialog, DialogTitle, DialogContent, 
  DialogActions, TextField, FormControl, InputLabel, Select, MenuItem
} from '@mui/material';
import {
  ArrowBack, Edit, Delete, Person, Schedule, Flag, Assignment,
  CheckCircle, PlayArrow
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { fetchTasks, updateTask, deleteTask } from '../store/slices/taskSlice';
import { fetchProjects } from '../store/slices/projectSlice';
import { useForm } from 'react-hook-form';

const TaskDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { tasks } = useSelector((state) => state.tasks);
  const { projects } = useSelector((state) => state.projects);
  
  const [editDialog, setEditDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);
  
  const { register, handleSubmit, setValue, formState: { errors } } = useForm();
  
  const task = tasks.find(t => t.id === parseInt(id));

  useEffect(() => {
    dispatch(fetchTasks());
    dispatch(fetchProjects());
  }, [dispatch]);

  useEffect(() => {
    if (task) {
      setValue('title', task.title);
      setValue('description', task.description);
      setValue('project_id', task.project?.id || '');
      setValue('priority', task.priority);
      setValue('status', task.status);
      setValue('assignee_id', task.assignee?.id || '');
      setValue('estimated_hours', task.estimated_hours || '');
      setValue('due_date', task.due_date ? new Date(task.due_date).toISOString().slice(0, 16) : '');
    }
  }, [task, setValue]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'todo': return 'default';
      case 'in_progress': return 'warning';
      case 'review': return 'info';
      case 'done': return 'success';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const formatDate = (dateString) => {
    return dateString ? new Date(dateString).toLocaleDateString() : 'Not set';
  };

  const handleUpdateTask = async (data) => {
    try {
      const taskData = {
        title: data.title,
        description: data.description || '',
        project_id: parseInt(data.project_id),
        priority: data.priority,
        status: data.status,
        due_date: data.due_date || null,
        estimated_hours: data.estimated_hours ? parseFloat(data.estimated_hours) : null,
      };

      if (data.assignee_id && data.assignee_id !== '') {
        taskData.assignee_id = parseInt(data.assignee_id);
      }

      await dispatch(updateTask({
        id: task.id,
        ...taskData
      })).unwrap();
      await dispatch(fetchTasks());
      setEditDialog(false);
    } catch (err) {
      console.error('Failed to update task:', err);
    }
  };

  const handleDeleteTask = async () => {
    try {
      await dispatch(deleteTask(task.id)).unwrap();
      setDeleteDialog(false);
      navigate('/tasks');
    } catch (err) {
      console.error('Failed to delete task:', err);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await dispatch(updateTask({
        id: task.id,
        status: newStatus
      })).unwrap();
      await dispatch(fetchTasks());
    } catch (err) {
      console.error('Failed to update task status:', err);
    }
  };

  if (!task) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" color="error">
          Task not found
        </Typography>
        <Button onClick={() => navigate('/tasks')} sx={{ mt: 2 }}>
          Back to Tasks
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <IconButton onClick={() => navigate('/tasks')} sx={{ mr: 1 }}>
            <ArrowBack />
          </IconButton>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              {task.title}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {task.description || 'No description provided'}
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
      </Box>

      {/* Task Info Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Task Information
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Status
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {['todo', 'in_progress', 'review', 'done'].map((status) => (
                        <Chip
                          key={status}
                          label={status.replace('_', ' ')}
                          color={getStatusColor(status)}
                          variant={task.status === status ? 'filled' : 'outlined'}
                          clickable
                          onClick={() => handleStatusChange(status)}
                          sx={{ 
                            textTransform: 'capitalize',
                            fontWeight: task.status === status ? 600 : 400,
                            cursor: 'pointer'
                          }}
                        />
                      ))}
                    </Box>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Priority
                    </Typography>
                    <Chip 
                      icon={<Flag />}
                      label={task.priority} 
                      color={getPriorityColor(task.priority)}
                      sx={{ textTransform: 'capitalize', fontWeight: 600 }}
                    />
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Project
                    </Typography>
                    <Typography variant="body1">
                      {task.project?.name || 'No project assigned'}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Assignee
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Person sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="body1">
                        {task.assignee?.username || 'Unassigned'}
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Due Date
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Schedule sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="body1">
                        {formatDate(task.due_date)}
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Estimated Hours
                    </Typography>
                    <Typography variant="body1">
                      {task.estimated_hours || 'Not estimated'}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {task.status !== 'done' && (
                  <Button
                    variant="contained"
                    startIcon={<CheckCircle />}
                    onClick={() => handleStatusChange('done')}
                    fullWidth
                    sx={{
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #059669 0%, #047857 100%)'
                      }
                    }}
                  >
                    Mark as Complete
                  </Button>
                )}
                {task.status !== 'in_progress' && task.status !== 'done' && (
                  <Button
                    variant="contained"
                    startIcon={<PlayArrow />}
                    onClick={() => handleStatusChange('in_progress')}
                    fullWidth
                    sx={{
                      background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)'
                      }
                    }}
                  >
                    Start Working
                  </Button>
                )}
                <Button
                  variant="outlined"
                  startIcon={<Assignment />}
                  onClick={() => navigate(`/tasks?project=${task.project?.id}`)}
                  fullWidth
                >
                  View Project Tasks
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

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
              Delete Task
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            Are you sure you want to delete <strong>{task.title}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This action cannot be undone. All data associated with this task will be permanently removed.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteTask} 
            color="error" 
            variant="contained"
            startIcon={<Delete />}
          >
            Delete Task
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Task</DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleSubmit(handleUpdateTask)} sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Task Title"
              margin="normal"
              {...register('title', { required: 'Title is required' })}
              error={!!errors.title}
              helperText={errors.title?.message}
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
              <InputLabel>Project</InputLabel>
              <Select
                {...register('project_id', { required: 'Project is required' })}
                error={!!errors.project_id}
              >
                {projects.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Priority</InputLabel>
              <Select
                {...register('priority')}
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Status</InputLabel>
              <Select
                {...register('status')}
              >
                <MenuItem value="todo">To Do</MenuItem>
                <MenuItem value="in_progress">In Progress</MenuItem>
                <MenuItem value="review">Review</MenuItem>
                <MenuItem value="done">Done</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              fullWidth
              label="Due Date"
              type="datetime-local"
              margin="normal"
              InputLabelProps={{ shrink: true }}
              {...register('due_date')}
            />
            
            <TextField
              fullWidth
              label="Assignee ID (optional)"
              type="number"
              margin="normal"
              placeholder="Leave empty to unassign"
              {...register('assignee_id')}
            />
            
            <TextField
              fullWidth
              label="Estimated Hours"
              type="number"
              margin="normal"
              inputProps={{ step: 0.5, min: 0 }}
              {...register('estimated_hours')}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmit(handleUpdateTask)} variant="contained">
            Update Task
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TaskDetail;