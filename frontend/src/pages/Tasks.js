import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  Button, 
  Chip, 
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { Add, Assignment, DragIndicator } from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { fetchTasks, createTask, updateTask } from '../store/slices/taskSlice';
import { fetchProjects } from '../store/slices/projectSlice';
import { fetchTeams } from '../store/slices/teamSlice';
import { useForm } from 'react-hook-form';
import UserPresence from '../components/UserPresence';
import webSocketService from '../services/websocket';
import api from '../services/api';
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import {
  useSortable,
} from '@dnd-kit/sortable';
import {CSS} from '@dnd-kit/utilities';

// Droppable Column Component
const DroppableColumn = ({ column, tasks, children }) => {
  const { setNodeRef, isOver } = useDroppable({
    id: column.key,
  });

  return (
    <Card 
      ref={setNodeRef}
      sx={{ 
        backgroundColor: column.color, 
        minHeight: '600px',
        border: isOver ? '2px solid #1976d2' : '1px solid #e0e0e0',
        transition: 'border-color 0.2s ease',
      }}
    >
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <Assignment sx={{ mr: 1 }} />
          {column.title} ({tasks.length})
        </Typography>
        {children}
      </CardContent>
    </Card>
  );
};

// Draggable Task Card Component
const DraggableTaskCard = ({ task, getPriorityColor, statusColumns, handleStatusChange }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <Card 
      ref={setNodeRef} 
      style={style} 
      sx={{ 
        mb: 2, 
        cursor: isDragging ? 'grabbing' : 'grab',
        position: 'relative'
      }}
      {...attributes}
      {...listeners}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
          <DragIndicator sx={{ color: 'text.secondary', mr: 1, mt: 0.5 }} />
          <Typography variant="subtitle1" gutterBottom sx={{ flexGrow: 1 }}>
            {task.title}
          </Typography>
        </Box>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {task.description?.substring(0, 100)}{task.description?.length > 100 ? '...' : ''}
        </Typography>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Chip 
            label={task.priority} 
            color={getPriorityColor(task.priority)}
            size="small"
          />
          <Typography variant="body2" color="text.secondary">
            {task.project?.name}
          </Typography>
        </Box>
        
        {task.assignee && (
          <Typography variant="body2" color="text.secondary">
            Assigned to: {task.assignee.username}
          </Typography>
        )}
        
        {task.due_date && (
          <Typography variant="body2" color="text.secondary">
            Due: {new Date(task.due_date).toLocaleDateString()}
          </Typography>
        )}

        {/* Status change buttons */}
        <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {statusColumns
            .filter(col => col.key !== task.status)
            .slice(0, 2) // Show only 2 quick actions to save space
            .map(col => (
              <Button
                key={col.key}
                size="small"
                variant="outlined"
                onClick={(e) => {
                  e.stopPropagation();
                  handleStatusChange(task.id, col.key);
                }}
              >
                → {col.title}
              </Button>
            ))}
        </Box>
      </CardContent>
    </Card>
  );
};

const Tasks = () => {
  const dispatch = useDispatch();
  const { tasks, isLoading, error } = useSelector((state) => state.tasks);
  const { projects } = useSelector((state) => state.projects);
  const { teams } = useSelector((state) => state.teams);
  const { user, token } = useSelector((state) => state.auth);
  const [openDialog, setOpenDialog] = useState(false);
  const [activeId, setActiveId] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);

  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    dispatch(fetchTasks());
    dispatch(fetchProjects());
    dispatch(fetchTeams());
  }, [dispatch]);

  // Set up real-time collaboration for selected project
  useEffect(() => {
    if (!selectedProject || !user || !token) return;

    // Update user presence to current project
    const updatePresence = async () => {
      try {
        await api.post('/collaboration/presence/update_presence/', {
          is_online: true,
          current_project: selectedProject
        });
      } catch (error) {
        console.error('Error updating presence:', error);
      }
    };

    updatePresence();

    const ws = webSocketService.connectToProject(selectedProject.toString(), token);
    
    const handleMessage = (data) => {
      if (data.type === 'task_updated') {
        // Refresh tasks when collaborative updates occur
        dispatch(fetchTasks());
      }
    };

    webSocketService.addMessageHandler('/ws/project/', selectedProject.toString(), handleMessage);

    return () => {
      webSocketService.removeMessageHandler('/ws/project/', selectedProject.toString(), handleMessage);
      webSocketService.disconnect('/ws/project/', selectedProject.toString());
    };
  }, [selectedProject, user, token, dispatch]);

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const handleCreateTask = async (data) => {
    try {
      const taskData = {
        title: data.title,
        description: data.description || '',
        project_id: parseInt(data.project_id),
        priority: data.priority || 'medium',
        status: 'todo',
        due_date: data.due_date || null,
        estimated_hours: data.estimated_hours ? parseFloat(data.estimated_hours) : null,
      };

      // Only include assignee_id if it exists and is valid
      if (data.assignee_id && data.assignee_id !== '') {
        taskData.assignee_id = parseInt(data.assignee_id);
      }

      await dispatch(createTask(taskData));
      setOpenDialog(false);
      reset();
    } catch (err) {
      console.error('Failed to create task:', err);
    }
  };

  const handleStatusChange = async (taskId, newStatus) => {
    console.log(`Updating task ${taskId} status to ${newStatus}`);

    try {
      // Use PATCH for partial update - only send the status
      const result = await dispatch(updateTask({ 
        id: taskId, 
        status: newStatus 
      }));
      
      if (updateTask.fulfilled.match(result)) {
        console.log('Task status updated successfully');
        
        // Send real-time update if project is selected
        if (selectedProject) {
          webSocketService.sendTaskUpdate(selectedProject.toString(), taskId, {
            status: newStatus,
            updated_by: user.username
          });
        }
      } else {
        console.error('Failed to update task status:', result.error);
      }
    } catch (err) {
      console.error('Failed to update task status:', err);
    }
  };

  const filteredTasks = selectedProject 
    ? tasks.filter(task => task.project?.id === selectedProject)
    : tasks;

  const tasksByStatus = {
    todo: filteredTasks.filter(task => task.status === 'todo'),
    in_progress: filteredTasks.filter(task => task.status === 'in_progress'),
    review: filteredTasks.filter(task => task.status === 'review'),
    done: filteredTasks.filter(task => task.status === 'done'),
  };

  const statusColumns = [
    { key: 'todo', title: 'To Do', color: '#f5f5f5' },
    { key: 'in_progress', title: 'In Progress', color: '#e3f2fd' },
    { key: 'review', title: 'Review', color: '#fff3e0' },
    { key: 'done', title: 'Done', color: '#e8f5e8' },
  ];

  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const activeId = active.id;
    const overId = over.id;

    // Find the task being dragged
    const draggedTask = filteredTasks.find(t => t.id === activeId);
    if (!draggedTask) return;

    // Check if we're dropping over a column
    const overColumn = statusColumns.find(col => col.key === overId);
    if (overColumn && draggedTask.status !== overColumn.key) {
      console.log(`Moving task ${activeId} from ${draggedTask.status} to ${overColumn.key}`);
      handleStatusChange(activeId, overColumn.key);
      return;
    }

    // Check if we're dropping over another task (to get the column)
    const overTask = filteredTasks.find(t => t.id === overId);
    if (overTask && draggedTask.status !== overTask.status) {
      console.log(`Moving task ${activeId} from ${draggedTask.status} to ${overTask.status}`);
      handleStatusChange(activeId, overTask.status);
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
          Error loading tasks: {error}
        </Typography>
      </Box>
    );
  }

  const activeTask = activeId ? filteredTasks.find(task => task.id === activeId) : null;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" gutterBottom>
            Tasks Board
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Filter by Project</InputLabel>
              <Select
                value={selectedProject || ''}
                onChange={(e) => setSelectedProject(e.target.value || null)}
                size="small"
              >
                <MenuItem value="">All Projects</MenuItem>
                {projects.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setOpenDialog(true)}
            >
              New Task
            </Button>
          </Box>
        </Box>

        {/* Online Users for Selected Project */}
        {selectedProject && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Collaborators Online
            </Typography>
            <UserPresence projectId={selectedProject} showLabels maxUsers={8} />
          </Box>
        )}

        {/* Kanban Board */}
        <Grid container spacing={2}>
          {statusColumns.map((column) => (
            <Grid item xs={12} md={3} key={column.key}>
              <DroppableColumn column={column} tasks={tasksByStatus[column.key]}>
                <SortableContext 
                  items={tasksByStatus[column.key].map(task => task.id)}
                  strategy={verticalListSortingStrategy}
                >
                  {tasksByStatus[column.key].map((task) => (
                    <DraggableTaskCard
                      key={task.id}
                      task={task}
                      getPriorityColor={getPriorityColor}
                      statusColumns={statusColumns}
                      handleStatusChange={handleStatusChange}
                    />
                  ))}
                </SortableContext>
              </DroppableColumn>
            </Grid>
          ))}
        </Grid>

        <DragOverlay>
          {activeTask ? (
            <Card sx={{ opacity: 0.8 }}>
              <CardContent sx={{ p: 2 }}>
                <Typography variant="subtitle1">
                  {activeTask.title}
                </Typography>
                <Chip 
                  label={activeTask.priority} 
                  color={getPriorityColor(activeTask.priority)}
                  size="small"
                />
              </CardContent>
            </Card>
          ) : null}
        </DragOverlay>

        {/* Create Task Dialog */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Create New Task</DialogTitle>
          <DialogContent>
            <Box component="form" onSubmit={handleSubmit(handleCreateTask)} sx={{ mt: 2 }}>
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
                  defaultValue="medium"
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
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
            <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
            <Button onClick={handleSubmit(handleCreateTask)} variant="contained">
              Create Task
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </DndContext>
  );
};

export default Tasks;