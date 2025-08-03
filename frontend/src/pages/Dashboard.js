import React, { useEffect } from 'react';
import {
  Grid, Typography, Box, Card, CardContent, LinearProgress, Avatar,
  Chip, IconButton, Button, Stack
} from '@mui/material';
import {
  People, Work, Assignment, CheckCircle, TrendingUp,
  Add, MoreVert, CalendarToday, Schedule
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { fetchProjects } from '../store/slices/projectSlice';
import { fetchTeams } from '../store/slices/teamSlice';
import { fetchTasks } from '../store/slices/taskSlice';

const Dashboard = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { projects } = useSelector((state) => state.projects);
  const { teams } = useSelector((state) => state.teams);
  const { tasks } = useSelector((state) => state.tasks);

  useEffect(() => {
    dispatch(fetchProjects());
    dispatch(fetchTeams());
    dispatch(fetchTasks());
  }, [dispatch]);

  // Calculate stats from real data
  const totalProjects = projects.length;
  const activeTasks = tasks.filter(task => task.status === 'in_progress' || task.status === 'todo').length;
  const totalMembers = teams.reduce((sum, team) => sum + (team.member_count || 0), 0);
  const completedTasks = tasks.filter(task => task.status === 'done').length;
  const activeProjects = projects.filter(project => project.status === 'active');

  const stats = [
    {
      title: 'Total Projects',
      value: totalProjects.toString(),
      icon: <Work />,
      color: '#1976d2',
    },
    {
      title: 'Active Tasks',
      value: activeTasks.toString(),
      icon: <Assignment />,
      color: '#ff9800',
    },
    {
      title: 'Team Members',
      value: totalMembers.toString(),
      icon: <People />,
      color: '#4caf50',
    },
    {
      title: 'Completed Tasks',
      value: completedTasks.toString(),
      icon: <CheckCircle />,
      color: '#9c27b0',
    },
  ];

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Good morning, {user?.username}! 👋
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here's what's happening with your projects today
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card 
              sx={{ 
                position: 'relative',
                overflow: 'visible',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  transition: 'all 0.2s ease-in-out',
                  boxShadow: '0 4px 12px 0 rgb(0 0 0 / 0.15)',
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 56,
                      height: 56,
                      borderRadius: 3,
                      background: `linear-gradient(135deg, ${stat.color}20 0%, ${stat.color}10 100%)`,
                      color: stat.color,
                    }}
                  >
                    {stat.icon}
                  </Box>
                  <IconButton size="small" sx={{ color: 'text.secondary' }}>
                    <MoreVert fontSize="small" />
                  </IconButton>
                </Box>
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: 'text.primary' }}>
                  {stat.value}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {stat.title}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TrendingUp sx={{ color: 'success.main', fontSize: 16 }} />
                  <Typography variant="caption" sx={{ color: 'success.main', fontWeight: 600 }}>
                    +12% from last month
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}

        <Grid item xs={12} md={8}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Recent Activities
                </Typography>
                <Button variant="outlined" size="small" startIcon={<Add />}>
                  View All
                </Button>
              </Box>
              <Stack spacing={3}>
                {(() => {
                  // Generate real recent activities from tasks and projects
                  const recentActivities = [];
                  
                  // Add recently completed tasks
                  const recentCompletedTasks = tasks
                    .filter(task => task.status === 'done')
                    .sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))
                    .slice(0, 2);
                  
                  recentCompletedTasks.forEach(task => {
                    const timeAgo = task.updated_at ? 
                      `${Math.floor((new Date() - new Date(task.updated_at)) / (1000 * 60 * 60))} hours ago` :
                      'Recently';
                    recentActivities.push({
                      user: task.assignee?.username || 'Someone',
                      action: 'completed task',
                      item: task.title,
                      time: timeAgo,
                      avatar: (task.assignee?.username || 'U')[0].toUpperCase()
                    });
                  });
                  
                  // Add recently created projects
                  const recentProjects = projects
                    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                    .slice(0, 2);
                  
                  recentProjects.forEach(project => {
                    const timeAgo = `${Math.floor((new Date() - new Date(project.created_at)) / (1000 * 60 * 60 * 24))} days ago`;
                    recentActivities.push({
                      user: project.owner?.username || user?.username || 'Someone',
                      action: 'created project',
                      item: project.name,
                      time: timeAgo,
                      avatar: (project.owner?.username || user?.username || 'U')[0].toUpperCase()
                    });
                  });
                  
                  // If no real activities, show a helpful message
                  if (recentActivities.length === 0) {
                    return (
                      <Box sx={{ textAlign: 'center', py: 4 }}>
                        <Assignment sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          No recent activities yet
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Start by creating tasks or projects to see activity here
                        </Typography>
                      </Box>
                    );
                  }
                  
                  return recentActivities.slice(0, 4).map((activity, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar sx={{ bgcolor: 'primary.main', width: 40, height: 40 }}>
                      {activity.avatar}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                        <strong>{activity.user}</strong> {activity.action} <strong>{activity.item}</strong>
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Schedule sx={{ fontSize: 14, color: 'text.secondary' }} />
                        <Typography variant="caption" color="text.secondary">
                          {activity.time}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                  ));
                })()}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Project Progress
                </Typography>
                <IconButton size="small">
                  <MoreVert fontSize="small" />
                </IconButton>
              </Box>
              <Stack spacing={3}>
                {activeProjects.length > 0 ? (
                  activeProjects.slice(0, 3).map((project) => {
                    // Calculate progress based on tasks completion
                    const projectTasks = tasks.filter(task => task.project?.id === project.id);
                    const completedProjectTasks = projectTasks.filter(task => task.status === 'done');
                    const progress = projectTasks.length > 0 
                      ? Math.round((completedProjectTasks.length / projectTasks.length) * 100)
                      : 0;
                    
                    return (
                      <Box key={project.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body1" sx={{ fontWeight: 600 }}>
                            {project.name}
                          </Typography>
                          <Chip 
                            label={`${progress}%`} 
                            size="small" 
                            color={progress >= 80 ? 'success' : progress >= 50 ? 'warning' : 'default'}
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={progress}
                          sx={{ 
                            height: 8, 
                            borderRadius: 4,
                            backgroundColor: 'grey.200',
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 4,
                              background: progress >= 80 ? 'linear-gradient(90deg, #10b981, #059669)' : 
                                         progress >= 50 ? 'linear-gradient(90deg, #f59e0b, #d97706)' : 
                                         'linear-gradient(90deg, #2563eb, #1e40af)'
                            }
                          }}
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          {completedProjectTasks.length}/{projectTasks.length} tasks completed
                        </Typography>
                      </Box>
                    );
                  })
                ) : (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Work sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      No active projects yet
                    </Typography>
                    <Button variant="contained" startIcon={<Add />} size="small">
                      Create Project
                    </Button>
                  </Box>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Upcoming Deadlines
                </Typography>
                <Button variant="text" endIcon={<CalendarToday />}>
                  View Calendar
                </Button>
              </Box>
              <Grid container spacing={2}>
                {(() => {
                  // Get tasks with due dates that are upcoming
                  const upcomingTasks = tasks
                    .filter(task => task.due_date && task.status !== 'done')
                    .map(task => {
                      const dueDate = new Date(task.due_date);
                      const now = new Date();
                      const daysDiff = Math.ceil((dueDate - now) / (1000 * 60 * 60 * 24));
                      
                      let deadlineText = '';
                      if (daysDiff < 0) {
                        deadlineText = `${Math.abs(daysDiff)} days overdue`;
                      } else if (daysDiff === 0) {
                        deadlineText = 'Today';
                      } else if (daysDiff === 1) {
                        deadlineText = 'Tomorrow';
                      } else if (daysDiff <= 7) {
                        deadlineText = `In ${daysDiff} days`;
                      } else {
                        deadlineText = `In ${Math.ceil(daysDiff / 7)} weeks`;
                      }
                      
                      return {
                        name: task.title,
                        deadline: deadlineText,
                        priority: task.priority,
                        project: task.project?.name || 'No Project',
                        daysDiff: daysDiff,
                        isOverdue: daysDiff < 0
                      };
                    })
                    .sort((a, b) => a.daysDiff - b.daysDiff) // Sort by urgency
                    .slice(0, 6); // Show up to 6 upcoming tasks
                  
                  if (upcomingTasks.length === 0) {
                    return (
                      <Grid item xs={12}>
                        <Box sx={{ textAlign: 'center', py: 4 }}>
                          <CalendarToday sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            No upcoming deadlines
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Tasks with due dates will appear here
                          </Typography>
                        </Box>
                      </Grid>
                    );
                  }
                  
                  return upcomingTasks.map((task, index) => (
                  <Grid item xs={12} md={4} key={index}>
                    <Box 
                      sx={{ 
                        p: 2, 
                        border: '1px solid', 
                        borderColor: 'divider', 
                        borderRadius: 2,
                        borderLeft: '4px solid',
                        borderLeftColor: task.isOverdue ? 'error.main' :
                                       task.priority === 'critical' ? 'error.main' :
                                       task.priority === 'high' ? 'error.main' : 
                                       task.priority === 'medium' ? 'warning.main' : 'success.main',
                        backgroundColor: task.isOverdue ? 'error.50' : 'background.paper'
                      }}
                    >
                      <Typography variant="body1" sx={{ fontWeight: 600, mb: 1 }}>
                        {task.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {task.project}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
                        <Chip 
                          label={task.deadline} 
                          size="small" 
                          color={task.isOverdue ? 'error' :
                                task.daysDiff === 0 ? 'warning' :
                                task.daysDiff === 1 ? 'warning' : 'default'}
                          variant={task.isOverdue ? 'filled' : 'outlined'}
                          sx={{ fontWeight: task.isOverdue ? 600 : 500 }}
                        />
                        <Chip 
                          label={task.priority} 
                          size="small" 
                          color={task.priority === 'critical' ? 'error' :
                                task.priority === 'high' ? 'error' : 
                                task.priority === 'medium' ? 'warning' : 'success'}
                        />
                      </Box>
                    </Box>
                  </Grid>
                  ));
                })()}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;