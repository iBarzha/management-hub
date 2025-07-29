import React, { useEffect, useState } from 'react';
import {Box, Typography, Grid, Card, CardContent, Button, Chip, CircularProgress, Dialog,
  DialogTitle, DialogContent, TextField, DialogActions, FormControl, InputLabel, Select, MenuItem} from '@mui/material';
import { 
  Add, Assignment, DragIndicator, MoreVert, Person, Schedule,
  Flag, CheckCircle, PlayArrow, Visibility, FilterList
} from '@mui/icons-material';
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

  const getColumnIcon = (key) => {
    switch (key) {
      case 'todo': return <Assignment />;
      case 'in_progress': return <PlayArrow />;
      case 'review': return <Visibility />;
      case 'done': return <CheckCircle />;
      default: return <Assignment />;
    }
  };

  return (
    <Box 
      ref={setNodeRef}
      sx={{ 
        backgroundColor: 'background.paper',
        borderRadius: 3,
        border: isOver ? `3px solid ${column.accentColor}` : '1px solid #e2e8f0',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        minHeight: '70vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: isOver ? 
          `0 20px 40px rgba(0, 0, 0, 0.15), 0 0 30px ${column.accentColor}30` : 
          '0 2px 8px rgba(0, 0, 0, 0.08)',
        transform: isOver ? 'scale(1.03) translateY(-2px)' : 'scale(1)',
        background: isOver ? 
          `linear-gradient(135deg, ${column.accentColor}15 0%, ${column.accentColor}05 100%)` : 
          'background.paper',
        position: 'relative',
        '&::before': isOver ? {
          content: '""',
          position: 'absolute',
          top: -1,
          left: -1,
          right: -1,
          bottom: -1,
          background: `linear-gradient(45deg, ${column.accentColor}, transparent, ${column.accentColor})`,
          borderRadius: 3,
          opacity: 0.6,
          zIndex: -1,
          animation: 'columnGlow 1.5s ease-in-out infinite alternate',
        } : {},
        '@keyframes columnGlow': {
          '0%': { opacity: 0.3 },
          '100%': { opacity: 0.7 }
        }
      }}
    >
      <Box sx={{ 
        p: 2, 
        borderBottom: '1px solid #e2e8f0',
        background: `linear-gradient(135deg, ${column.accentColor}15 0%, ${column.accentColor}05 100%)`
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ 
              p: 0.5, 
              borderRadius: 1.5, 
              backgroundColor: column.accentColor + '20',
              color: column.accentColor 
            }}>
              {getColumnIcon(column.key)}
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 600, color: 'text.primary' }}>
              {column.title}
            </Typography>
          </Box>
          <Chip 
            label={tasks.length} 
            size="small" 
            sx={{ 
              backgroundColor: column.accentColor + '20',
              color: column.accentColor,
              fontWeight: 600
            }} 
          />
        </Box>
      </Box>
      <Box sx={{ p: 2, flexGrow: 1, overflowY: 'auto' }}>
        {children}
      </Box>
    </Box>
  );
};

// Draggable Task Card Component
const DraggableTaskCard = ({ task, getPriorityColor, statusColumns, handleStatusChange, successAnimations }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ 
    id: task.id,
    animateLayoutChanges: () => false // Disable layout animations to prevent snap-back
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition: 'none', // No transitions at all
    opacity: isDragging ? 0 : 1,
    pointerEvents: isDragging ? 'none' : 'auto',
  };

  const getPriorityBorderColor = (priority) => {
    switch (priority) {
      case 'critical': return '#ef4444';
      case 'high': return '#f59e0b';
      case 'medium': return '#2563eb';
      case 'low': return '#10b981';
      default: return '#64748b';
    }
  };

  return (
    <Card 
      ref={setNodeRef} 
      style={style} 
      sx={{ 
        mb: 2, 
        cursor: isDragging ? 'grabbing' : 'grab',
        position: 'relative',
        borderLeft: `4px solid ${getPriorityBorderColor(task.priority)}`,
        transition: isDragging ? 'none' : 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        transformOrigin: 'center',
        '&:hover': {
          boxShadow: isDragging ? undefined : 
            `0 12px 30px rgba(0, 0, 0, 0.15), 
             0 0 20px ${getPriorityBorderColor(task.priority)}20`,
          transform: isDragging ? undefined : 'translateY(-4px) scale(1.02)',
        },
        '&:active': {
          transform: isDragging ? undefined : 'translateY(-2px) scale(0.98)',
        },
        // Success animation
        ...(successAnimations[task.id] && {
          animation: 'successPulse 0.6s ease-out',
          '@keyframes successPulse': {
            '0%': { 
              transform: 'scale(1)',
              boxShadow: `0 0 0 0 ${getPriorityBorderColor(task.priority)}40`
            },
            '50%': { 
              transform: 'scale(1.05)',
              boxShadow: `0 0 0 10px ${getPriorityBorderColor(task.priority)}20`
            },
            '100%': { 
              transform: 'scale(1)',
              boxShadow: `0 0 0 0 ${getPriorityBorderColor(task.priority)}00`
            }
          }
        })
      }}
      {...attributes}
      {...listeners}
    >
      <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="subtitle1" sx={{ 
              fontWeight: 600, 
              mb: 0.5,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden'
            }}>
              {task.title}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
              {task.project?.name}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <DragIndicator sx={{ color: 'text.secondary', fontSize: 16 }} />
            <MoreVert sx={{ color: 'text.secondary', fontSize: 16 }} />
          </Box>
        </Box>
        
        {task.description && (
          <Typography 
            variant="body2" 
            color="text.secondary" 
            sx={{ 
              mb: 2,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              lineHeight: 1.4
            }}
          >
            {task.description}
          </Typography>
        )}
        
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          <Chip 
            icon={<Flag sx={{ fontSize: 14 }} />}
            label={task.priority} 
            color={getPriorityColor(task.priority)}
            size="small"
            sx={{ fontWeight: 500, '& .MuiChip-label': { px: 1 } }}
          />
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 1.5, borderTop: '1px solid #e2e8f0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {task.assignee ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Person sx={{ fontSize: 14, color: 'text.secondary' }} />
                <Typography variant="caption" color="text.secondary">
                  {task.assignee.username}
                </Typography>
              </Box>
            ) : (
              <Typography variant="caption" color="text.secondary">
                Unassigned
              </Typography>
            )}
          </Box>
          {task.due_date && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Schedule sx={{ fontSize: 14, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">
                {new Date(task.due_date).toLocaleDateString()}
              </Typography>
            </Box>
          )}
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
  const [optimisticUpdates, setOptimisticUpdates] = useState({});
  const [successAnimations, setSuccessAnimations] = useState({});

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
        return Promise.resolve();
      } else {
        console.error('Failed to update task status:', result.error);
        return Promise.reject(result.error);
      }
    } catch (err) {
      console.error('Failed to update task status:', err);
      return Promise.reject(err);
    }
  };

  const filteredTasks = selectedProject 
    ? tasks.filter(task => task.project?.id === selectedProject)
    : tasks;

  // Apply optimistic updates to tasks
  const tasksWithOptimisticUpdates = filteredTasks.map(task => {
    if (optimisticUpdates[task.id]) {
      return { ...task, status: optimisticUpdates[task.id] };
    }
    return task;
  });

  const tasksByStatus = {
    todo: tasksWithOptimisticUpdates.filter(task => task.status === 'todo'),
    in_progress: tasksWithOptimisticUpdates.filter(task => task.status === 'in_progress'),
    review: tasksWithOptimisticUpdates.filter(task => task.status === 'review'),
    done: tasksWithOptimisticUpdates.filter(task => task.status === 'done'),
  };

  const statusColumns = [
    { key: 'todo', title: 'To Do', color: '#f8fafc', accentColor: '#64748b' },
    { key: 'in_progress', title: 'In Progress', color: '#eff6ff', accentColor: '#2563eb' },
    { key: 'review', title: 'Review', color: '#fffbeb', accentColor: '#f59e0b' },
    { key: 'done', title: 'Done', color: '#f0fdf4', accentColor: '#10b981' },
  ];

  const handleDragStart = (event) => {
    setActiveId(event.active.id);
    // Add a subtle haptic feedback (if supported)
    if (navigator.vibrate) {
      navigator.vibrate(50);
    }
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    
    if (!over) {
      setActiveId(null);
      return;
    }

    const activeId = active.id;
    const overId = over.id;

    // Find the task being dragged
    const draggedTask = filteredTasks.find(t => t.id === activeId);
    if (!draggedTask) return;

    // Check if we're dropping over a column
    const overColumn = statusColumns.find(col => col.key === overId);
    if (overColumn && draggedTask.status !== overColumn.key) {
      console.log(`Moving task ${activeId} from ${draggedTask.status} to ${overColumn.key}`);
      // Optimistically update the UI immediately
      setOptimisticUpdates(prev => ({ ...prev, [activeId]: overColumn.key }));
      // Clear active immediately to prevent snap-back animation
      setActiveId(null);
      // Make the actual API call
      handleStatusChange(activeId, overColumn.key).then(() => {
        // Add success animation
        setSuccessAnimations(prev => ({ ...prev, [activeId]: true }));
        setTimeout(() => {
          setSuccessAnimations(prev => {
            const updated = { ...prev };
            delete updated[activeId];
            return updated;
          });
        }, 600);
        
        // Clear optimistic update after API success
        setOptimisticUpdates(prev => {
          const updated = { ...prev };
          delete updated[activeId];
          return updated;
        });
      }).catch(() => {
        // Revert optimistic update on error
        setOptimisticUpdates(prev => {
          const updated = { ...prev };
          delete updated[activeId];
          return updated;
        });
      });
      return;
    }

    // Check if we're dropping over another task (to get the column)
    const overTask = filteredTasks.find(t => t.id === overId);
    if (overTask && draggedTask.status !== overTask.status) {
      console.log(`Moving task ${activeId} from ${draggedTask.status} to ${overTask.status}`);
      // Optimistically update the UI immediately
      setOptimisticUpdates(prev => ({ ...prev, [activeId]: overTask.status }));
      // Clear active immediately to prevent snap-back animation
      setActiveId(null);
      // Make the actual API call
      handleStatusChange(activeId, overTask.status).then(() => {
        // Add success animation
        setSuccessAnimations(prev => ({ ...prev, [activeId]: true }));
        setTimeout(() => {
          setSuccessAnimations(prev => {
            const updated = { ...prev };
            delete updated[activeId];
            return updated;
          });
        }, 600);
        
        // Clear optimistic update after API success
        setOptimisticUpdates(prev => {
          const updated = { ...prev };
          delete updated[activeId];
          return updated;
        });
      }).catch(() => {
        // Revert optimistic update on error
        setOptimisticUpdates(prev => {
          const updated = { ...prev };
          delete updated[activeId];
          return updated;
        });
      });
      return;
    }
    
    // If no status change, just clear the active state
    setActiveId(null);
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
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                Task Board
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Organize and track your tasks with an intuitive Kanban board
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Button
                variant="outlined"
                startIcon={<FilterList />}
                sx={{ borderRadius: 2 }}
              >
                Filters
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
                New Task
              </Button>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 3 }}>
            <FormControl sx={{ minWidth: 220 }}>
              <InputLabel>Filter by Project</InputLabel>
              <Select
                value={selectedProject || ''}
                onChange={(e) => setSelectedProject(e.target.value || null)}
                size="small"
                sx={{ borderRadius: 2 }}
              >
                <MenuItem value="">All Projects</MenuItem>
                {projects.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            {filteredTasks.length > 0 && (
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  {filteredTasks.length} tasks
                </Typography>
                <Typography variant="body2" color="text.secondary">•</Typography>
                <Typography variant="body2" color="text.secondary">
                  {tasksByStatus.done.length} completed
                </Typography>
              </Box>
            )}
          </Box>
        </Box>

        {/* Online Users for Selected Project */}
        {selectedProject && (
          <Card sx={{ mb: 3, border: '1px solid #e2e8f0' }}>
            <CardContent sx={{ py: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Team Collaboration
                </Typography>
                <UserPresence projectId={selectedProject} showLabels maxUsers={8} />
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Kanban Board */}
        <Box sx={{ display: 'flex', gap: 3, overflowX: 'auto', pb: 2 }}>
          {statusColumns.map((column) => (
            <Box key={column.key} sx={{ minWidth: 280, flexShrink: 0 }}>
              <DroppableColumn column={column} tasks={tasksByStatus[column.key]}>
                <SortableContext 
                  items={tasksByStatus[column.key].map(task => task.id)}
                  strategy={verticalListSortingStrategy}
                >
                  {tasksByStatus[column.key].length === 0 ? (
                    <Box sx={{ 
                      textAlign: 'center', 
                      py: 4, 
                      color: 'text.secondary',
                      border: '2px dashed #e2e8f0',
                      borderRadius: 2,
                      backgroundColor: 'background.paper'
                    }}>
                      <Assignment sx={{ fontSize: 32, mb: 1, opacity: 0.5 }} />
                      <Typography variant="body2" sx={{ opacity: 0.7 }}>
                        No tasks in {column.title.toLowerCase()}
                      </Typography>
                    </Box>
                  ) : (
                    tasksByStatus[column.key].map((task) => (
                      <DraggableTaskCard
                        key={task.id}
                        task={task}
                        getPriorityColor={getPriorityColor}
                        statusColumns={statusColumns}
                        handleStatusChange={handleStatusChange}
                        successAnimations={successAnimations}
                      />
                    ))
                  )}
                </SortableContext>
              </DroppableColumn>
            </Box>
          ))}
        </Box>

        <DragOverlay
          dropAnimation={null}
          style={{
            cursor: 'grabbing',
          }}
        >
          {activeTask ? (
            <Card sx={{ 
              opacity: 0.95,
              transform: 'rotate(5deg) scale(1.08)',
              boxShadow: `
                0 30px 60px rgba(0, 0, 0, 0.25),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                0 0 40px ${activeTask.priority === 'critical' ? 'rgba(239, 68, 68, 0.3)' : 
                           activeTask.priority === 'high' ? 'rgba(245, 158, 11, 0.3)' :
                           activeTask.priority === 'medium' ? 'rgba(37, 99, 235, 0.3)' : 'rgba(16, 185, 129, 0.3)'}
              `,
              borderLeft: `4px solid ${activeTask.priority === 'critical' ? '#ef4444' : 
                                      activeTask.priority === 'high' ? '#f59e0b' :
                                      activeTask.priority === 'medium' ? '#2563eb' : '#10b981'}`,
              borderRadius: 3,
              background: `
                linear-gradient(135deg, 
                  rgba(255, 255, 255, 0.95) 0%, 
                  rgba(255, 255, 255, 0.9) 100%
                ),
                linear-gradient(135deg,
                  ${activeTask.priority === 'critical' ? 'rgba(239, 68, 68, 0.05)' : 
                    activeTask.priority === 'high' ? 'rgba(245, 158, 11, 0.05)' :
                    activeTask.priority === 'medium' ? 'rgba(37, 99, 235, 0.05)' : 'rgba(16, 185, 129, 0.05)'} 0%,
                  transparent 100%
                )
              `,
              backdropFilter: 'blur(20px)',
              cursor: 'grabbing',
              pointerEvents: 'none',
              transition: 'none',
              position: 'relative',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: -2,
                left: -2,
                right: -2,
                bottom: -2,
                background: `linear-gradient(45deg, 
                  ${activeTask.priority === 'critical' ? '#ef4444' : 
                    activeTask.priority === 'high' ? '#f59e0b' :
                    activeTask.priority === 'medium' ? '#2563eb' : '#10b981'}, 
                  transparent, 
                  ${activeTask.priority === 'critical' ? '#ef4444' : 
                    activeTask.priority === 'high' ? '#f59e0b' :
                    activeTask.priority === 'medium' ? '#2563eb' : '#10b981'}
                )`,
                borderRadius: 3,
                opacity: 0.3,
                zIndex: -1,
                animation: 'dragGlow 2s ease-in-out infinite alternate',
              },
              '@keyframes dragGlow': {
                '0%': { 
                  opacity: 0.3,
                  transform: 'scale(1)',
                },
                '100%': { 
                  opacity: 0.6,
                  transform: 'scale(1.02)',
                }
              }
            }}>
              <CardContent sx={{ p: 3, position: 'relative', zIndex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="subtitle1" sx={{ 
                    fontWeight: 700, 
                    color: 'text.primary',
                    textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)',
                    lineHeight: 1.3
                  }}>
                    {activeTask.title}
                  </Typography>
                  <DragIndicator sx={{ 
                    color: activeTask.priority === 'critical' ? '#ef4444' : 
                           activeTask.priority === 'high' ? '#f59e0b' :
                           activeTask.priority === 'medium' ? '#2563eb' : '#10b981',
                    fontSize: 20,
                    opacity: 0.8
                  }} />
                </Box>
                
                {activeTask.description && (
                  <Typography 
                    variant="body2" 
                    color="text.secondary" 
                    sx={{ 
                      mb: 2,
                      opacity: 0.8,
                      display: '-webkit-box',
                      WebkitLineClamp: 1,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                  >
                    {activeTask.description}
                  </Typography>
                )}
                
                <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', flexWrap: 'wrap' }}>
                  <Chip 
                    icon={<Flag sx={{ fontSize: 14 }} />}
                    label={activeTask.priority} 
                    color={getPriorityColor(activeTask.priority)}
                    size="small"
                    sx={{ 
                      fontWeight: 600,
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
                      '& .MuiChip-label': { px: 1.5 }
                    }}
                  />
                  {activeTask.project && (
                    <Chip
                      label={activeTask.project.name}
                      size="small"
                      variant="outlined"
                      sx={{ 
                        fontWeight: 500,
                        backgroundColor: 'rgba(255, 255, 255, 0.8)',
                        '& .MuiChip-label': { px: 1.5 }
                      }}
                    />
                  )}
                  {activeTask.assignee && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 1 }}>
                      <Person sx={{ fontSize: 14, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                        {activeTask.assignee.username}
                      </Typography>
                    </Box>
                  )}
                </Box>
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