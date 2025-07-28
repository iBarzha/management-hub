import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  Divider
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';
import { useSelector } from 'react-redux';
import webSocketService from '../services/websocket';
import api from '../services/api';

const Chat = ({ room, height = 400 }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [typingUsers, setTypingUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const { user, token } = useSelector(state => state.auth);

  const loadChatHistory = async () => {
    try {
      const response = await api.get(`/collaboration/messages/?room=${room}`);
      const messages = Array.isArray(response.data) 
        ? response.data 
        : (response.data?.results || []);
      setMessages(messages.reverse());
      setLoading(false);
    } catch (error) {
      console.error('Error loading chat history:', error);
      setMessages([]);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!room || !token) return;

    // Load chat history
    loadChatHistory();

    // Connect to WebSocket
    const ws = webSocketService.connectToChat(room, token);
    
    // Add message handler
    const handleMessage = (data) => {
      if (!data || typeof data !== 'object') {
        console.warn('Invalid message data received:', data);
        return;
      }
      
      switch (data.type) {
        case 'chat_message':
          setMessages(prev => [data, ...prev]);
          break;
        case 'user_joined':
          setOnlineUsers(Array.isArray(data.online_users) ? data.online_users : []);
          break;
        case 'user_left':
          setOnlineUsers(Array.isArray(data.online_users) ? data.online_users : []);
          break;
        case 'typing':
          if (data.user && typeof data.is_typing === 'boolean') {
            handleTypingIndicator(data.user, data.is_typing);
          }
          break;
        default:
          console.log('Unknown message type:', data.type);
      }
    };

    webSocketService.addMessageHandler('/ws/chat/', room, handleMessage);

    return () => {
      webSocketService.removeMessageHandler('/ws/chat/', room, handleMessage);
      webSocketService.disconnect('/ws/chat/', room);
    };
  }, [room, token, loadChatHistory]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleTypingIndicator = (username, isTyping) => {
    if (isTyping) {
      setTypingUsers(prev => [...prev.filter(u => u !== username), username]);
    } else {
      setTypingUsers(prev => prev.filter(u => u !== username));
    }
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    webSocketService.sendChatMessage(room, newMessage.trim());
    setNewMessage('');
    
    // Stop typing indicator
    webSocketService.sendTypingIndicator(room, false);
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
  };

  const handleTyping = (e) => {
    setNewMessage(e.target.value);
    
    // Send typing indicator
    webSocketService.sendTypingIndicator(room, true);
    
    // Clear previous timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    // Stop typing after 2 seconds of inactivity
    typingTimeoutRef.current = setTimeout(() => {
      webSocketService.sendTypingIndicator(room, false);
    }, 2000);
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getUserInitials = (username) => {
    return username.substring(0, 2).toUpperCase();
  };

  if (loading) {
    return (
      <Paper sx={{ p: 2, height }}>
        <Typography>Loading chat...</Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ display: 'flex', flexDirection: 'column', height }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" gutterBottom>
          Chat: {room}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {onlineUsers.map((username) => (
            <Chip
              key={username}
              label={username}
              size="small"
              color={username === user.username ? 'primary' : 'default'}
              avatar={<Avatar sx={{ width: 20, height: 20, fontSize: '0.7rem' }}>
                {getUserInitials(username)}
              </Avatar>}
            />
          ))}
        </Box>
      </Box>

      {/* Messages */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
        <List dense>
          {messages.map((message, index) => (
            <ListItem key={index} alignItems="flex-start">
              <ListItemAvatar>
                <Avatar sx={{ width: 32, height: 32, fontSize: '0.8rem' }}>
                  {getUserInitials(message.user)}
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle2" component="span">
                      {message.user}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatTimestamp(message.timestamp)}
                    </Typography>
                  </Box>
                }
                secondary={message.message}
              />
            </ListItem>
          ))}
          
          {/* Typing indicators */}
          {typingUsers.length > 0 && (
            <>
              <Divider />
              <ListItem>
                <ListItemText
                  secondary={
                    <Typography variant="caption" color="text.secondary" fontStyle="italic">
                      {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
                    </Typography>
                  }
                />
              </ListItem>
            </>
          )}
        </List>
        <div ref={messagesEndRef} />
      </Box>

      {/* Message input */}
      <Box component="form" onSubmit={handleSendMessage} sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Type a message..."
            value={newMessage}
            onChange={handleTyping}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage(e);
              }
            }}
          />
          <IconButton 
            type="submit" 
            color="primary" 
            disabled={!newMessage.trim()}
            sx={{ minWidth: 40 }}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Paper>
  );
};

export default Chat;