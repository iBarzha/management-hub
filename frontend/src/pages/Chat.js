import React, { useState } from 'react';
import {Container, Paper, Typography, Grid, TextField, Button, Box, List, ListItem, ListItemText, Divider
} from '@mui/material';
import { useSelector } from 'react-redux';
import Chat from '../components/Chat';
import UserPresence from '../components/UserPresence';

const ChatPage = () => {
  const [selectedRoom, setSelectedRoom] = useState('general');
  const [newRoom, setNewRoom] = useState('');
  const { user } = useSelector(state => state.auth);

  const predefinedRooms = [
    { id: 'general', name: 'General Discussion' },
    { id: 'development', name: 'Development' },
    { id: 'design', name: 'Design' },
    { id: 'testing', name: 'Testing' },
    { id: 'announcements', name: 'Announcements' },
  ];

  const handleCreateRoom = () => {
    if (newRoom.trim()) {
      setSelectedRoom(newRoom.toLowerCase().replace(/\s+/g, '-'));
      setNewRoom('');
    }
  };

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom>
        Team Chat
      </Typography>
      
      <Box sx={{ mb: 3 }}>
        <UserPresence showLabels maxUsers={10} />
      </Box>

      <Grid container spacing={3} sx={{ height: 'calc(100vh - 200px)' }}>
        {/* Room List */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Chat Rooms
              </Typography>
              
              {/* Create Room */}
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  size="small"
                  placeholder="New room name"
                  value={newRoom}
                  onChange={(e) => setNewRoom(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleCreateRoom();
                    }
                  }}
                />
                <Button 
                  variant="contained" 
                  size="small" 
                  onClick={handleCreateRoom}
                  disabled={!newRoom.trim()}
                >
                  Create
                </Button>
              </Box>
              
              <Divider />
            </Box>
            
            {/* Room List */}
            <List dense sx={{ flex: 1, overflow: 'auto' }}>
              {predefinedRooms.map((room) => (
                <ListItem
                  key={room.id}
                  button
                  selected={selectedRoom === room.id}
                  onClick={() => setSelectedRoom(room.id)}
                >
                  <ListItemText 
                    primary={room.name}
                    secondary={`#${room.id}`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Chat Area */}
        <Grid item xs={12} md={9}>
          <Chat room={selectedRoom} height="100%" />
        </Grid>
      </Grid>
    </Container>
  );
};

export default ChatPage;