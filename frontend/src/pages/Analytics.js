import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Tab,
  Tabs,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  Paper
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  Group as GroupIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  DateRange as DateRangeIcon
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import api from '../services/api';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement
);

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Analytics = () => {
  const [tabValue, setTabValue] = useState(0);
  const [selectedProject, setSelectedProject] = useState('');
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [burndownData, setBurndownData] = useState(null);
  const [velocityData, setVelocityData] = useState(null);
  const [teamPerformance, setTeamPerformance] = useState(null);
  const [dateRange, setDateRange] = useState(30); // days

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadAnalyticsData();
    }
  }, [selectedProject, dateRange]);

  const loadProjects = async () => {
    try {
      const response = await api.get('/api/projects/');
      setProjects(response.data.results || response.data);
      if (response.data.results?.length > 0 || response.data.length > 0) {
        const firstProject = response.data.results?.[0] || response.data[0];
        setSelectedProject(firstProject.id);
      }
    } catch (error) {
      console.error('Error loading projects:', error);
      setError('Failed to load projects');
    }
  };

  const loadAnalyticsData = async () => {
    if (!selectedProject) return;
    
    setLoading(true);
    setError('');
    
    try {
      // Load dashboard data
      const dashboardResponse = await api.get(
        `/api/analytics/projects/${selectedProject}/dashboard/?days=${dateRange}`
      );
      setDashboardData(dashboardResponse.data);

      // Load burndown data
      const burndownResponse = await api.get(
        `/api/analytics/projects/${selectedProject}/burndown/?days=${dateRange}`
      );
      setBurndownData(burndownResponse.data);

      // Load velocity data
      const velocityResponse = await api.get(
        `/api/analytics/projects/${selectedProject}/velocity/?weeks=12`
      );
      setVelocityData(velocityResponse.data);

      // Load team performance
      const teamResponse = await api.get(
        `/api/analytics/projects/${selectedProject}/team-performance/?days=${dateRange}`
      );
      setTeamPerformance(teamResponse.data);

    } catch (error) {
      console.error('Error loading analytics data:', error);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshMetrics = async () => {
    if (!selectedProject) return;
    
    setLoading(true);
    try {
      await api.post(`/api/analytics/projects/${selectedProject}/metrics/refresh/`);
      await loadAnalyticsData();
    } catch (error) {
      console.error('Error refreshing metrics:', error);
      setError('Failed to refresh metrics');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    if (!selectedProject) return;
    
    try {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - dateRange);
      
      const response = await api.post('/api/analytics/reports/generate/', {
        project_id: selectedProject,
        report_type: 'project_summary',
        export_format: format,
        date_from: startDate.toISOString(),
        date_to: endDate.toISOString()
      }, {
        responseType: format === 'csv' ? 'blob' : 'json'
      });

      if (format === 'csv') {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `analytics_report_${Date.now()}.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      }
    } catch (error) {
      console.error('Error exporting report:', error);
      setError('Failed to export report');
    }
  };

  // Chart configurations
  const getBurndownChartConfig = () => {
    if (!burndownData?.burndown_data) return null;

    const data = burndownData.burndown_data;
    return {
      labels: data.map(d => new Date(d.date).toLocaleDateString()),
      datasets: [
        {
          label: 'Remaining Tasks',
          data: data.map(d => d.remaining_tasks),
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          tension: 0.1
        },
        {
          label: 'Ideal Burndown',
          data: data.map(d => d.ideal_remaining_tasks),
          borderColor: 'rgb(54, 162, 235)',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderDash: [5, 5],
          tension: 0.1
        }
      ]
    };
  };

  const getVelocityChartConfig = () => {
    if (!velocityData?.velocity_trend?.velocity_data) return null;

    const data = velocityData.velocity_trend.velocity_data;
    return {
      labels: data.map(d => `Week ${new Date(d.week_start).toLocaleDateString()}`),
      datasets: [
        {
          label: 'Tasks Completed',
          data: data.map(d => d.tasks_completed),
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1
        },
        {
          label: 'Story Points Completed',
          data: data.map(d => d.story_points_completed),
          backgroundColor: 'rgba(153, 102, 255, 0.6)',
          borderColor: 'rgba(153, 102, 255, 1)',
          borderWidth: 1
        }
      ]
    };
  };

  const getTaskBreakdownChartConfig = () => {
    if (!dashboardData?.task_breakdown) return null;

    const breakdown = dashboardData.task_breakdown;
    const labels = breakdown.map(item => item.status.charAt(0).toUpperCase() + item.status.slice(1));
    const data = breakdown.map(item => item.count);
    
    return {
      labels,
      datasets: [
        {
          data,
          backgroundColor: [
            '#FF6384',
            '#36A2EB',
            '#FFCE56',
            '#4BC0C0',
            '#9966FF'
          ],
          hoverBackgroundColor: [
            '#FF6384',
            '#36A2EB',
            '#FFCE56',
            '#4BC0C0',
            '#9966FF'
          ]
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top'
      },
      title: {
        display: true
      }
    },
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  const selectedProjectData = projects.find(p => p.id === selectedProject);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <AnalyticsIcon sx={{ mr: 2, fontSize: 40, color: 'primary.main' }} />
          <Typography variant="h4">Analytics & Reporting</Typography>
        </Box>
        
        <Box display="flex" alignItems="center" gap={2}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Project</InputLabel>
            <Select
              value={selectedProject}
              label="Project"
              onChange={(e) => setSelectedProject(e.target.value)}
            >
              {projects.map((project) => (
                <MenuItem key={project.id} value={project.id}>
                  {project.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Date Range</InputLabel>
            <Select
              value={dateRange}
              label="Date Range"
              onChange={(e) => setDateRange(e.target.value)}
            >
              <MenuItem value={7}>7 days</MenuItem>
              <MenuItem value={30}>30 days</MenuItem>
              <MenuItem value={90}>90 days</MenuItem>
              <MenuItem value={180}>6 months</MenuItem>
            </Select>
          </FormControl>
          
          <Tooltip title="Refresh Metrics">
            <IconButton onClick={handleRefreshMetrics} disabled={loading || !selectedProject}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => handleExport('csv')}
            disabled={loading || !selectedProject}
            size="small"
          >
            Export CSV
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {selectedProject && (
        <>
          {/* Project Overview Cards */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography color="textSecondary" gutterBottom>
                        Total Tasks
                      </Typography>
                      <Typography variant="h4">
                        {dashboardData?.metrics?.total_tasks || 0}
                      </Typography>
                    </Box>
                    <AssessmentIcon color="primary" sx={{ fontSize: 40 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography color="textSecondary" gutterBottom>
                        Completion Rate
                      </Typography>
                      <Typography variant="h4">
                        {dashboardData?.metrics?.completion_percentage?.toFixed(1) || 0}%
                      </Typography>
                    </Box>
                    <TrendingUpIcon color="success" sx={{ fontSize: 40 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography color="textSecondary" gutterBottom>
                        Current Velocity
                      </Typography>
                      <Typography variant="h4">
                        {dashboardData?.metrics?.current_velocity?.toFixed(1) || 0}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        tasks/week
                      </Typography>
                    </Box>
                    <TimelineIcon color="info" sx={{ fontSize: 40 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography color="textSecondary" gutterBottom>
                        Team Members
                      </Typography>
                      <Typography variant="h4">
                        {dashboardData?.metrics?.active_team_members || 0}
                      </Typography>
                    </Box>
                    <GroupIcon color="secondary" sx={{ fontSize: 40 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Tabs for different analytics views */}
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
                <Tab label="Overview" />
                <Tab label="Burndown Chart" />
                <Tab label="Velocity Tracking" />
                <Tab label="Team Performance" />
              </Tabs>
            </Box>

            <TabPanel value={tabValue} index={0}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                  <Typography variant="h6" gutterBottom>
                    Task Status Breakdown
                  </Typography>
                  {loading ? (
                    <Box display="flex" justifyContent="center" p={4}>
                      <CircularProgress />
                    </Box>
                  ) : getTaskBreakdownChartConfig() ? (
                    <Doughnut 
                      data={getTaskBreakdownChartConfig()} 
                      options={{
                        responsive: true,
                        plugins: {
                          legend: {
                            position: 'right'
                          }
                        }
                      }}
                    />
                  ) : (
                    <Typography color="textSecondary">No data available</Typography>
                  )}
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Typography variant="h6" gutterBottom>
                    Project Health
                  </Typography>
                  <Box display="flex" flexDirection="column" gap={2}>
                    <Chip 
                      label={`On-time Rate: ${dashboardData?.metrics?.on_time_completion_rate?.toFixed(1) || 0}%`}
                      color={dashboardData?.metrics?.on_time_completion_rate > 80 ? 'success' : 'warning'}
                    />
                    <Chip 
                      label={`Overdue Tasks: ${dashboardData?.metrics?.overdue_tasks || 0}`}
                      color={dashboardData?.metrics?.overdue_tasks > 0 ? 'error' : 'success'}
                    />
                    <Chip 
                      label={`Avg. Completion Time: ${dashboardData?.metrics?.average_task_completion_time?.toFixed(1) || 0}h`}
                      color="info"
                    />
                  </Box>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <Typography variant="h6" gutterBottom>
                Burndown Chart
              </Typography>
              {loading ? (
                <Box display="flex" justifyContent="center" p={4}>
                  <CircularProgress />
                </Box>
              ) : getBurndownChartConfig() ? (
                <Line data={getBurndownChartConfig()} options={chartOptions} />
              ) : (
                <Typography color="textSecondary">No burndown data available</Typography>
              )}
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <Typography variant="h6" gutterBottom>
                Velocity Tracking
              </Typography>
              {loading ? (
                <Box display="flex" justifyContent="center" p={4}>
                  <CircularProgress />
                </Box>
              ) : getVelocityChartConfig() ? (
                <Bar data={getVelocityChartConfig()} options={chartOptions} />
              ) : (
                <Typography color="textSecondary">No velocity data available</Typography>
              )}
              
              {velocityData?.velocity_trend && (
                <Box mt={3}>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h6">
                          {velocityData.velocity_trend.average_tasks_per_week?.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Avg Tasks/Week
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={4}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h6">
                          {velocityData.velocity_trend.average_points_per_week?.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Avg Points/Week
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={4}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h6">
                          {velocityData.velocity_trend.total_weeks}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Weeks Tracked
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </TabPanel>

            <TabPanel value={tabValue} index={3}>
              <Typography variant="h6" gutterBottom>
                Team Performance
              </Typography>
              {loading ? (
                <Box display="flex" justifyContent="center" p={4}>
                  <CircularProgress />
                </Box>
              ) : teamPerformance?.team_performance ? (
                <Grid container spacing={2}>
                  {teamPerformance.team_performance.map((member, index) => (
                    <Grid item xs={12} md={6} lg={4} key={index}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            {member.user_name || member.user_email}
                          </Typography>
                          <Typography variant="body2" color="textSecondary" gutterBottom>
                            {member.role}
                          </Typography>
                          
                          <Box display="flex" justifyContent="space-between" mt={2}>
                            <Typography variant="body2">
                              Tasks Assigned: <strong>{member.tasks_assigned}</strong>
                            </Typography>
                          </Box>
                          <Box display="flex" justifyContent="space-between">
                            <Typography variant="body2">
                              Tasks Completed: <strong>{member.tasks_completed}</strong>
                            </Typography>
                          </Box>
                          <Box display="flex" justifyContent="space-between">
                            <Typography variant="body2">
                              Completion Rate: <strong>{member.completion_rate?.toFixed(1)}%</strong>
                            </Typography>
                          </Box>
                          <Box display="flex" justifyContent="space-between">
                            <Typography variant="body2">
                              On-time Rate: <strong>{member.on_time_rate?.toFixed(1)}%</strong>
                            </Typography>
                          </Box>
                          
                          <Box mt={2}>
                            <Chip 
                              label={`Productivity Score: ${member.productivity_score?.toFixed(1)}`}
                              color={member.productivity_score > 80 ? 'success' : member.productivity_score > 60 ? 'warning' : 'error'}
                              size="small"
                            />
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Typography color="textSecondary">No team performance data available</Typography>
              )}
            </TabPanel>
          </Card>
        </>
      )}
    </Box>
  );
};

export default Analytics;