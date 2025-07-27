import React, { useEffect } from 'react';
import { Box, Typography, Grid, Card, CardContent, Button, Avatar, Chip, CircularProgress } from '@mui/material';
import { Add, People } from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { fetchTeams } from '../store/slices/teamSlice';

const Teams = () => {
  const dispatch = useDispatch();
  const { teams, isLoading, error } = useSelector((state) => state.teams);

  useEffect(() => {
    dispatch(fetchTeams());
  }, [dispatch]);


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
          <Button variant="contained" startIcon={<Add />}>
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
    </Box>
  );
};

export default Teams;