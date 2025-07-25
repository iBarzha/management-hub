import React from 'react';
import {Grid, Paper, Typography, Box, Card, CardContent, LinearProgress,} from '@mui/material';
import {People, Work, Assignment, CheckCircle} from '@mui/icons-material';
import { useSelector } from 'react-redux';

const Dashboard = () => {
  const { user } = useSelector((state) => state.auth);

  const stats = [
    {
      title: 'Total Projects',
      value: '12',
      icon: <Work />,
      color: '#1976d2',
    },
    {
      title: 'Active Tasks',
      value: '24',
      icon: <Assignment />,
      color: '#ff9800',
    },
    {
      title: 'Team Members',
      value: '8',
      icon: <People />,
      color: '#4caf50',
    },
    {
      title: 'Completed',
      value: '156',
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
              <Typography variant="body2">Project Alpha</Typography>
              <LinearProgress
                variant="determinate"
                value={75}
                sx={{ mt: 1, mb: 2 }}
              />
              <Typography variant="body2">Project Beta</Typography>
              <LinearProgress
                variant="determinate"
                value={45}
                sx={{ mt: 1, mb: 2 }}
              />
              <Typography variant="body2">Project Gamma</Typography>
              <LinearProgress
                variant="determinate"
                value={90}
                sx={{ mt: 1 }}
              />
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;