import React, { useEffect } from 'react';
import {Grid, Paper, Typography, Box, Card, CardContent, LinearProgress,} from '@mui/material';
import {People, Work, Assignment, CheckCircle} from '@mui/icons-material';
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
      <Typography variant="h4" gutterBottom>
        Welcome back, {user?.username}!
      </Typography>

      <Grid container spacing={3} sx={{ mt: 1 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 50,
                      height: 50,
                      borderRadius: '50%',
                      backgroundColor: `${stat.color}20`,
                      color: stat.color,
                      mr: 2,
                    }}
                  >
                    {stat.icon}
                  </Box>
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {stat.title}
                    </Typography>
                    <Typography variant="h5" component="div">
                      {stat.value}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}

        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activities
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="textSecondary">
                No recent activities to show
              </Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Project Progress
            </Typography>
            <Box sx={{ mt: 2 }}>
              {activeProjects.length > 0 ? (
                activeProjects.slice(0, 3).map((project) => {
                  // Calculate progress based on tasks completion
                  const projectTasks = tasks.filter(task => task.project?.id === project.id);
                  const completedProjectTasks = projectTasks.filter(task => task.status === 'done');
                  const progress = projectTasks.length > 0 
                    ? Math.round((completedProjectTasks.length / projectTasks.length) * 100)
                    : 0;
                  
                  return (
                    <Box key={project.id} sx={{ mb: 2 }}>
                      <Typography variant="body2">{project.name}</Typography>
                      <LinearProgress
                        variant="determinate"
                        value={progress}
                        sx={{ mt: 1 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {progress}% complete ({completedProjectTasks.length}/{projectTasks.length} tasks)
                      </Typography>
                    </Box>
                  );
                })
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No active projects to display
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;