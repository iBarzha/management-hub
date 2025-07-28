import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  Button, 
  Avatar, 
  Chip, 
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import { Add, People } from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { fetchTeams, createTeam } from '../store/slices/teamSlice';
import { useForm } from 'react-hook-form';

const Teams = () => {
  const dispatch = useDispatch();
  const { teams, isLoading, error } = useSelector((state) => state.teams);
  const [openDialog, setOpenDialog] = useState(false);
  
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Teams
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          sx={{ mb: 2 }}
          onClick={() => setOpenDialog(true)}
        >
          New Team
        </Button>
      </Box>

      {teams.length === 0 ? (
        <Box textAlign="center" py={8}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No teams found
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Create your first team to start collaborating
          </Typography>
          <Button variant="contained" startIcon={<Add />} onClick={() => setOpenDialog(true)}>
            Create Team
          </Button>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {teams.map((team) => (
            <Grid item xs={12} md={6} lg={4} key={team.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                      <People />
                    </Avatar>
                    <Box>
                      <Typography variant="h6" component="div">
                        {team.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {team.member_count} members
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {team.description}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Chip 
                      label="active"
                      color="success"
                      size="small"
                    />
                    <Button size="small" variant="outlined">
                      View Details
                    </Button>
                  </Box>
                </CardContent>
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
    </Box>
  );
};

export default Teams;