import React, { useEffect, useState } from 'react';
import {Box, Typography, Grid, Card, CardContent, Button, Chip, CircularProgress, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, Menu, MenuItem} from '@mui/material';
import { 
  Add, People, MoreVert, Group, PersonAdd,
  Work, Assignment, Star, TrendingUp
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { fetchTeams, createTeam } from '../store/slices/teamSlice';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

const Teams = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { teams, isLoading, error } = useSelector((state) => state.teams);
  const [openDialog, setOpenDialog] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedTeam, setSelectedTeam] = useState(null);
  
  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  useEffect(() => {
    dispatch(fetchTeams());
  }, [dispatch]);

  const handleCreateTeam = async (data) => {
    try {
      await dispatch(createTeam(data));
      setOpenDialog(false);
      reset();
    } catch (err) {
      console.error('Failed to create team:', err);
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
          Error loading teams: {error}
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
              Teams
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Collaborate with your team members across projects
            </Typography>
          </Box>
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
            New Team
          </Button>
        </Box>
        
        {teams.length > 0 && (
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <Chip
              label={`${teams.length} Teams`}
              color="primary"
              variant="filled"
              sx={{ borderRadius: 2 }}
            />
            <Chip
              label={`${teams.reduce((sum, team) => sum + (team.member_count || 0), 0)} Total Members`}
              variant="outlined"
              sx={{ borderRadius: 2 }}
            />
          </Box>
        )}
      </Box>

      {teams.length === 0 ? (
        <Card sx={{ textAlign: 'center', py: 8 }}>
          <CardContent>
            <Group sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
              No teams yet
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 400, mx: 'auto' }}>
              Teams help you organize members, assign roles, and collaborate effectively on projects.
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
              Create Your First Team
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {teams.map((team, index) => (
            <Grid item xs={12} md={6} lg={4} key={team.id}>
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
                onClick={() => navigate(`/teams/${team.id}`)}
              >
                <CardContent sx={{ flexGrow: 1, p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box
                        sx={{
                          width: 56,
                          height: 56,
                          borderRadius: 3,
                          background: `linear-gradient(135deg, ${index % 2 === 0 ? '#2563eb' : '#7c3aed'}20 0%, ${index % 2 === 0 ? '#2563eb' : '#7c3aed'}10 100%)`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: index % 2 === 0 ? '#2563eb' : '#7c3aed',
                        }}
                      >
                        <People fontSize="large" />
                      </Box>
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                          {team.name}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                          <Group sx={{ fontSize: 14, color: 'text.secondary' }} />
                          <Typography variant="caption" color="text.secondary">
                            {team.member_count || 0} members
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                    <Button 
                      size="small" 
                      sx={{ minWidth: 'auto', p: 0.5 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setAnchorEl(e.currentTarget);
                        setSelectedTeam(team);
                      }}
                    >
                      <MoreVert fontSize="small" />
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
                      minHeight: '2.5rem',
                      lineHeight: 1.4
                    }}
                  >
                    {team.description || 'No description provided'}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 1, mb: 3, flexWrap: 'wrap' }}>
                    <Chip 
                      label="Active"
                      color="success"
                      size="small"
                      sx={{ fontWeight: 500 }}
                    />
                    {index === 0 && (
                      <Chip 
                        icon={<Star sx={{ fontSize: 14 }} />}
                        label="Featured"
                        color="warning"
                        size="small"
                        sx={{ fontWeight: 500 }}
                      />
                    )}
                  </Box>
                  
                  <Box sx={{ display: 'flex', gap: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flex: 1 }}>
                      <Work sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">
                        {Math.floor(Math.random() * 5) + 1} projects
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flex: 1 }}>
                      <Assignment sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">
                        {Math.floor(Math.random() * 20) + 5} tasks
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flex: 1 }}>
                      <TrendingUp sx={{ fontSize: 16, color: 'success.main' }} />
                      <Typography variant="caption" sx={{ color: 'success.main', fontWeight: 600 }}>
                        {Math.floor(Math.random() * 30) + 70}%
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
                
                <Box sx={{ p: 2, pt: 0 }}>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button 
                      variant="outlined" 
                      size="small" 
                      startIcon={<PersonAdd />}
                      sx={{ flex: 1, borderRadius: 1.5 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        console.log('Invite members to team:', team.name);
                        // Navigate to team invite page or open invite modal
                      }}
                    >
                      Invite
                    </Button>
                    <Button 
                      variant="contained" 
                      size="small" 
                      sx={{ 
                        flex: 1, 
                        borderRadius: 1.5,
                        background: index % 2 === 0 ? 'linear-gradient(135deg, #2563eb, #1e40af)' : 'linear-gradient(135deg, #7c3aed, #5b21b6)'
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/teams/${team.id}/manage`);
                      }}
                    >
                      Manage
                    </Button>
                  </Box>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Team Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Team</DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleSubmit(handleCreateTeam)} sx={{ mt: 2 }}>
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
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmit(handleCreateTeam)} variant="contained">
            Create Team
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
        <MenuItem onClick={() => {
          navigate(`/teams/${selectedTeam?.id}`);
          setAnchorEl(null);
        }}>View Details</MenuItem>
        <MenuItem onClick={() => {
          console.log('Edit team:', selectedTeam?.name);
          setAnchorEl(null);
        }}>Edit Team</MenuItem>
        <MenuItem onClick={() => {
          navigate(`/teams/${selectedTeam?.id}/members`);
          setAnchorEl(null);
        }}>Manage Members</MenuItem>
        <MenuItem onClick={() => {
          navigate(`/projects?team=${selectedTeam?.id}`);
          setAnchorEl(null);
        }}>View Projects</MenuItem>
        <MenuItem onClick={() => {
          console.log('Delete team:', selectedTeam?.name);
          setAnchorEl(null);
        }}>Delete Team</MenuItem>
      </Menu>
    </Box>
  );
};

export default Teams;