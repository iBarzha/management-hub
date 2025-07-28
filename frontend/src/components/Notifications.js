import React, { useState, useEffect } from 'react';
import {
  IconButton,
  Badge,
  Menu,
  MenuItem,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Box,
  Button,
  Chip
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Task as TaskIcon,
  Group as GroupIcon,
  Schedule as ScheduleIcon,
  Comment as CommentIcon,
  AlternateEmail as MentionIcon,
  Circle as CircleIcon
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { toast } from 'react-toastify';
import webSocketService from '../services/websocket';
import api from '../services/api';

const NotificationTypeIcons = {
  task_assigned: TaskIcon,
  task_updated: TaskIcon,
  project_updated: GroupIcon,
  sprint_started: ScheduleIcon,
  sprint_ended: ScheduleIcon,
  deadline_reminder: ScheduleIcon,
  comment_added: CommentIcon,
  mention: MentionIcon,
};

const Notifications = () => {
  const [anchorEl, setAnchorEl] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const { user, token } = useSelector(state => state.auth);
  const open = Boolean(anchorEl);

  useEffect(() => {
    if (!user || !token) return;

    // Load initial notifications
    loadNotifications();
    loadUnreadCount();

    // Connect to WebSocket for real-time notifications
    const ws = webSocketService.connectToNotifications(user.id, token);
    
    const handleMessage = (data) => {
      if (data.type === 'notification') {
        // Add to notifications list
        setNotifications(prev => [data, ...prev]);
        setUnreadCount(prev => prev + 1);
        
        // Show toast
        toast.info(data.title, {
          position: "top-right",
          autoClose: 5000,
        });
      }
    };

    webSocketService.addMessageHandler('/ws/notifications/', user.id, handleMessage);

    return () => {
      webSocketService.removeMessageHandler('/ws/notifications/', user.id, handleMessage);
      webSocketService.disconnect('/ws/notifications/', user.id);
    };
  }, [user, token]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await api.get('/collaboration/notifications/');
      setNotifications(response.data.results || []);
    } catch (error) {
      console.error('Error loading notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const response = await api.get('/collaboration/notifications/unread_count/');
      setUnreadCount(response.data.count || 0);
    } catch (error) {
      console.error('Error loading unread count:', error);
    }
  };

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const markAsRead = async (notificationId) => {
    try {
      await api.post(`/collaboration/notifications/${notificationId}/mark_read/`);
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.post('/collaboration/notifications/mark_all_read/');
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  const getNotificationIcon = (type) => {
    const IconComponent = NotificationTypeIcons[type] || CircleIcon;
    return <IconComponent fontSize="small" />;
  };

  const getNotificationColor = (type) => {
    switch (type) {
      case 'task_assigned':
      case 'mention':
        return 'primary';
      case 'deadline_reminder':
        return 'warning';
      case 'sprint_started':
      case 'sprint_ended':
        return 'success';
      default:
        return 'default';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <>
      <IconButton
        color="inherit"
        onClick={handleClick}
        sx={{ ml: 2 }}
      >
        <Badge badgeContent={unreadCount} color="error">
          <NotificationsIcon />
        </Badge>
      </IconButton>
      
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: { width: 360, maxHeight: 480 }
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            Notifications
          </Typography>
          {unreadCount > 0 && (
            <Button size="small" onClick={markAllAsRead}>
              Mark all read
            </Button>
          )}
        </Box>
        
        <Divider />
        
        {loading ? (
          <MenuItem>
            <Typography color="text.secondary">Loading...</Typography>
          </MenuItem>
        ) : notifications.length === 0 ? (
          <MenuItem>
            <Typography color="text.secondary">No notifications</Typography>
          </MenuItem>
        ) : (
          <List dense sx={{ maxHeight: 360, overflow: 'auto' }}>
            {notifications.slice(0, 10).map((notification) => (
              <ListItem
                key={notification.id}
                onClick={() => !notification.read && markAsRead(notification.id)}
                sx={{
                  cursor: notification.read ? 'default' : 'pointer',
                  backgroundColor: notification.read ? 'transparent' : 'action.hover',
                  '&:hover': {
                    backgroundColor: 'action.selected',
                  }
                }}
              >
                <ListItemIcon>
                  {getNotificationIcon(notification.notification_type)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle2" sx={{ flex: 1 }}>
                        {notification.title}
                      </Typography>
                      <Chip
                        size="small"
                        label={notification.notification_type.replace('_', ' ')}
                        color={getNotificationColor(notification.notification_type)}
                        sx={{ fontSize: '0.7rem', height: 20 }}
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                        {notification.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatTimestamp(notification.created_at)}
                      </Typography>
                    </Box>
                  }
                />
                {!notification.read && (
                  <Box sx={{ ml: 1 }}>
                    <CircleIcon color="primary" sx={{ fontSize: 8 }} />
                  </Box>
                )}
              </ListItem>
            ))}
          </List>
        )}
        
        {notifications.length > 10 && (
          <>
            <Divider />
            <MenuItem onClick={handleClose}>
              <Typography color="primary" sx={{ width: '100%', textAlign: 'center' }}>
                View all notifications
              </Typography>
            </MenuItem>
          </>
        )}
      </Menu>
    </>
  );
};

export default Notifications;