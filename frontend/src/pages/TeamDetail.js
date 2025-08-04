import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, Button, Chip, Avatar, AvatarGroup,
  Tab, Tabs, Grid, IconButton, Menu, MenuItem, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, List, ListItem, ListItemAvatar,
  ListItemText, ListItemSecondaryAction
} from '@mui/material';
import {
  ArrowBack, Edit, Delete, MoreVert, People, Assignment, Work,
  PersonAdd, Email, Phone, AdminPanelSettings, Group, Star,
  TrendingUp, Add
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { fetchTeams } from '../store/slices/teamSlice';
import { fetchProjects } from '../store/slices/projectSlice';
import { fetchTasks } from '../store/slices/taskSlice';
import { useForm } from 'react-hook-form';

const TeamDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { teams } = useSelector((state) => state.teams);
  const { projects } = useSelector((state) => state.projects);
  const { tasks } = useSelector((state) => state.tasks);
  
  const [tabValue, setTabValue] = useState(0);
  const [anchorEl, setAnchorEl] = useState(null);
  const [editDialog, setEditDialog] = useState(false);
  const [inviteDialog, setInviteDialog] = useState(false);
  
  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm();
  
  const team = teams.find(t => t.id === parseInt(id));
  const teamProjects = projects.filter(project => project.team?.id === parseInt(id));
  const teamTasks = tasks.filter(task => teamProjects.some(project => project.id === task.project?.id));
  const completedTasks = teamTasks.filter(task => task.status === 'done');

  // Mock team members data (in real app, this would come from API)
  const teamMembers = [
    { id: 1, name: 'John Doe', email: 'john@example.com', role: 'Team Lead', avatar: 'JD', status: 'online' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'Developer', avatar: 'JS', status: 'away' },
    { id: 3, name: 'Mike Johnson', email: 'mike@example.com', role: 'Designer', avatar: 'MJ', status: 'offline' },
  ];

  useEffect(() => {
    dispatch(fetchTeams());
    dispatch(fetchProjects());
    dispatch(fetchTasks());
  }, [dispatch]);

  useEffect(() => {
    if (team) {
      setValue('name', team.name);
      setValue('description', team.description);
    }
  }, [team, setValue]);

  const handleUpdateTeam = async (data) => {
    try {
      console.log('Updating team:', data);
      // Here you would dispatch an update action
      setEditDialog(false);
    } catch (err) {
      console.error('Failed to update team:', err);
    }
  };

  const handleInviteMember = async (data) => {
    try {
      console.log('Inviting member:', data);
      // Here you would dispatch an invite action
      setInviteDialog(false);
      reset();
    } catch (err) {
      console.error('Failed to invite member:', err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'success';
      case 'away': return 'warning';
      case 'offline': return 'default';
      default: return 'default';
    }
  };

  if (!team) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" color="error">
          Team not found
        </Typography>
        <Button onClick={() => navigate('/teams')} sx={{ mt: 2 }}>
          Back to Teams
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <IconButton onClick={() => navigate('/teams')} sx={{ mr: 1 }}>
            <ArrowBack />
          </IconButton>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
              {team.name}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {team.description || 'No description provided'}
            </Typography>
          </Box>
          <IconButton
            onClick={(e) => setAnchorEl(e.currentTarget)}
            sx={{ ml: 2 }}
          >
            <MoreVert />
          </IconButton>
        </Box>

        {/* Team Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <People sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {teamMembers.length}
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
                <Work sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {teamProjects.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Projects
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Assignment sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {teamTasks.length}
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
                <TrendingUp sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {teamTasks.length > 0 ? Math.round((completedTasks.length / teamTasks.length) * 100) : 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Completion Rate
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Team Info Card */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Status
                  </Typography>
                  <Chip 
                    label="Active" 
                    color="success"
                    sx={{ fontWeight: 600 }}
                  />
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Team Lead
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar sx={{ width: 24, height: 24, fontSize: 12 }}>JD</Avatar>
                    <Typography variant="body1">John Doe</Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Created Date
                  </Typography>
                  <Typography variant="body1">
                    {new Date().toLocaleDateString()}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Active Members
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AvatarGroup max={4} sx={{ '& .MuiAvatar-root': { width: 24, height: 24, fontSize: 12 } }}>
                      {teamMembers.filter(m => m.status === 'online').map(member => (
                        <Avatar key={member.id}>{member.avatar}</Avatar>
                      ))}
                    </AvatarGroup>
                    <Typography variant="body2" color="text.secondary">
                      {teamMembers.filter(m => m.status === 'online').length} online
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Box>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab label="Members" />
            <Tab label="Projects" />
            <Tab label="Activity" />
          </Tabs>
        </Box>
        
        <CardContent>
          {tabValue === 0 && (
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6">Team Members</Typography>
                <Button
                  variant="contained"
                  startIcon={<PersonAdd />}
                  onClick={() => setInviteDialog(true)}
                >
                  Invite Member
                </Button>
              </Box>
              
              <List>
                {teamMembers.map((member) => (
                  <ListItem key={member.id} divider>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        {member.avatar}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {member.name}
                          </Typography>
                          <Chip
                            label={member.status}
                            size="small"
                            color={getStatusColor(member.status)}
                            sx={{ ml: 1 }}
                          />
                          {member.role === 'Team Lead' && (
                            <Star sx={{ color: 'warning.main', fontSize: 16 }} />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {member.role}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {member.email}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton onClick={() => console.log('Member options for', member.name)}>
                        <MoreVert />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
          
          {tabValue === 1 && (
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6">Team Projects</Typography>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => navigate('/projects')}
                >
                  New Project
                </Button>
              </Box>
              
              {teamProjects.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Work sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No projects yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Create projects to organize your team's work
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => navigate('/projects')}
                  >
                    Create First Project
                  </Button>
                </Box>
              ) : (
                <Grid container spacing={2}>
                  {teamProjects.map((project) => (
                    <Grid item xs={12} md={6} key={project.id}>
                      <Card 
                        variant="outlined" 
                        sx={{ 
                          cursor: 'pointer',
                          '&:hover': { boxShadow: 2 }
                        }}
                        onClick={() => navigate(`/projects/${project.id}`)}
                      >
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                            <Work color="primary" />
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              {project.name}
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            {project.description || 'No description'}
                          </Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Chip 
                              label={project.status.replace('_', ' ')} 
                              size="small"
                              color={project.status === 'active' ? 'success' : 'default'}
                              sx={{ textTransform: 'capitalize' }}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {new Date(project.created_at).toLocaleDateString()}
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </Box>
          )}
          
          {tabValue === 2 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Assignment sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Activity feed coming soon
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={() => {
          setEditDialog(true);
          setAnchorEl(null);
        }}>
          <Edit sx={{ mr: 1 }} /> Edit Team
        </MenuItem>
        <MenuItem onClick={() => {
          setInviteDialog(true);
          setAnchorEl(null);
        }}>
          <PersonAdd sx={{ mr: 1 }} /> Invite Members
        </MenuItem>
        <MenuItem onClick={() => {
          navigate(`/projects?team=${team.id}`);
          setAnchorEl(null);
        }}>
          <Work sx={{ mr: 1 }} /> View Projects
        </MenuItem>
        <MenuItem onClick={() => {
          console.log('Delete team');
          setAnchorEl(null);
        }}>
          <Delete sx={{ mr: 1 }} /> Delete Team
        </MenuItem>
      </Menu>

      {/* Edit Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Team</DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleSubmit(handleUpdateTeam)} sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Team Name"
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
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmit(handleUpdateTeam)} variant="contained">
            Update Team
          </Button>
        </DialogActions>
      </Dialog>

      {/* Invite Member Dialog */}
      <Dialog open={inviteDialog} onClose={() => setInviteDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Invite Team Member</DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleSubmit(handleInviteMember)} sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Email Address"
              type="email"
              margin="normal"
              {...register('email', { 
                required: 'Email is required',
                pattern: {
                  value: /^\S+@\S+$/i,
                  message: 'Invalid email address'
                }
              })}
              error={!!errors.email}
              helperText={errors.email?.message}
            />
            
            <TextField
              fullWidth
              label="Role (Optional)"
              margin="normal"
              placeholder="e.g., Developer, Designer, Project Manager"
              {...register('role')}
            />
            
            <TextField
              fullWidth
              label="Personal Message (Optional)"
              margin="normal"
              multiline
              rows={3}
              placeholder="Add a personal message to the invitation..."
              {...register('message')}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmit(handleInviteMember)} variant="contained">
            Send Invitation
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TeamDetail;