import React, { useState, useEffect } from 'react';
import {Avatar, AvatarGroup, Tooltip, Badge, Box, Typography, Chip} from '@mui/material';
import { Circle as CircleIcon } from '@mui/icons-material';
import { useSelector } from 'react-redux';
import api from '../services/api';

const UserPresence = ({ projectId, maxUsers = 5, showLabels = false }) => {
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useSelector(state => state.auth);

  useEffect(() => {
    loadOnlineUsers();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadOnlineUsers, 30000);
    
    return () => clearInterval(interval);
  }, [projectId]);

  const loadOnlineUsers = async () => {
    try {
      const url = projectId 
        ? `/collaboration/presence/online_users/?project_id=${projectId}`
        : '/collaboration/presence/online_users/';
      
      const response = await api.get(url);
      const users = Array.isArray(response.data) ? response.data : (response.data?.results || []);
      setOnlineUsers(users);
      setLoading(false);
    } catch (error) {
      console.error('Error loading online users:', error);
      setOnlineUsers([]);
      setLoading(false);
    }
  };

  const getUserInitials = (username) => {
    return username.substring(0, 2).toUpperCase();
  };

  const getUserColor = (username) => {
    // Generate consistent color based on username
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
      hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = hash % 360;
    return `hsl(${hue}, 70%, 50%)`;
  };

  if (loading) {
    return null;
  }

  if (onlineUsers.length === 0) {
    return showLabels ? (
      <Typography variant="caption" color="text.secondary">
        No users online
      </Typography>
    ) : null;
  }

  const displayUsers = onlineUsers.slice(0, maxUsers);
  const extraCount = onlineUsers.length - maxUsers;

  if (showLabels) {
    return (
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {onlineUsers.map((presence) => (
          <Chip
            key={presence.user.id}
            avatar={
              <Badge
                overlap="circular"
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                badgeContent={
                  <CircleIcon 
                    sx={{ 
                      fontSize: 8, 
                      color: 'success.main',
                      backgroundColor: 'white',
                      borderRadius: '50%'
                    }} 
                  />
                }
              >
                <Avatar 
                  sx={{ 
                    width: 24, 
                    height: 24, 
                    fontSize: '0.7rem',
                    bgcolor: getUserColor(presence.user.username)
                  }}
                >
                  {getUserInitials(presence.user.username)}
                </Avatar>
              </Badge>
            }
            label={presence.user.username}
            size="small"
            color={presence.user.id === user.id ? 'primary' : 'default'}
            sx={{ height: 32 }}
          />
        ))}
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <AvatarGroup max={maxUsers} sx={{ '& .MuiAvatar-root': { width: 32, height: 32, fontSize: '0.8rem' } }}>
        {displayUsers.map((presence) => (
          <Tooltip key={presence.user.id} title={`${presence.user.username} (Online)`}>
            <Badge
              overlap="circular"
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              badgeContent={
                <CircleIcon 
                  sx={{ 
                    fontSize: 10, 
                    color: 'success.main',
                    backgroundColor: 'white',
                    borderRadius: '50%',
                    border: '1px solid white'
                  }} 
                />
              }
            >
              <Avatar 
                sx={{ 
                  bgcolor: getUserColor(presence.user.username),
                  border: presence.user.id === user.id ? '2px solid' : 'none',
                  borderColor: 'primary.main'
                }}
              >
                {getUserInitials(presence.user.username)}
              </Avatar>
            </Badge>
          </Tooltip>
        ))}
        {extraCount > 0 && (
          <Tooltip title={`${extraCount} more users online`}>
            <Avatar sx={{ bgcolor: 'grey.400' }}>
              +{extraCount}
            </Avatar>
          </Tooltip>
        )}
      </AvatarGroup>
      
      {onlineUsers.length > 0 && (
        <Typography variant="caption" color="text.secondary">
          {onlineUsers.length} online
        </Typography>
      )}
    </Box>
  );
};

export default UserPresence;