import React, { useState, useEffect, useRef } from 'react';
import {Box, Card, CardContent, TextField, IconButton, Typography, List, ListItem, ListItemText, ListItemAvatar,
  Avatar, Chip, Divider, Badge, Stack} from '@mui/material';
import { 
  Send as SendIcon, 
  Circle as CircleIcon,
  EmojiEmotions,
  AttachFile
} from '@mui/icons-material';
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
      <Card sx={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            Loading chat messages...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ display: 'flex', flexDirection: 'column', height, overflow: 'hidden' }}>
      {/* Header */}
      <Box sx={{ 
        p: 3, 
        borderBottom: '1px solid #e2e8f0',
        background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Team Chat
          </Typography>
          <Badge 
            badgeContent={onlineUsers.length} 
            color="success"
            sx={{
              '& .MuiBadge-badge': {
                backgroundColor: '#10b981',
                color: 'white'
              }
            }}
          >
            <Typography variant="body2" color="text.secondary">
              Online
            </Typography>
          </Badge>
        </Box>
        
        <Stack direction="row" spacing={1} sx={{ overflowX: 'auto', pb: 1 }}>
          {onlineUsers.map((username) => (
            <Chip
              key={username}
              label={username}
              size="small"
              color={username === user?.username ? 'primary' : 'default'}
              variant={username === user?.username ? 'filled' : 'outlined'}
              avatar={
                <Badge
                  overlap="circular"
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  badgeContent={
                    <CircleIcon sx={{ 
                      fontSize: 8, 
                      color: '#10b981',
                      backgroundColor: 'white',
                      borderRadius: '50%'
                    }} />
                  }
                >
                  <Avatar sx={{ width: 20, height: 20, fontSize: '0.7rem', bgcolor: 'primary.main' }}>
                    {getUserInitials(username)}
                  </Avatar>
                </Badge>
              }
              sx={{ 
                borderRadius: 2,
                '& .MuiChip-label': { fontWeight: 500 }
              }}
            />
          ))}
        </Stack>
      </Box>

      {/* Messages */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2, backgroundColor: '#fafafa' }}>
        {messages.length === 0 ? (
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            height: '100%',
            textAlign: 'center'
          }}>
            <Typography variant="body2" color="text.secondary">
              No messages yet. Start the conversation!
            </Typography>
          </Box>
        ) : (
          <Stack spacing={2}>
            {messages.map((message, index) => {
              const isOwnMessage = message.user === user?.username;
              const prevMessage = messages[index - 1];
              const isNewSender = !prevMessage || prevMessage.user !== message.user;
              
              return (
                <Box
                  key={index}
                  sx={{
                    display: 'flex',
                    flexDirection: isOwnMessage ? 'row-reverse' : 'row',
                    alignItems: 'flex-end',
                    gap: 1,
                    mt: isNewSender ? 2 : 0.5
                  }}
                >
                  {!isOwnMessage && isNewSender && (
                    <Avatar 
                      sx={{ 
                        width: 32, 
                        height: 32, 
                        fontSize: '0.8rem',
                        bgcolor: 'primary.main'
                      }}
                    >
                      {getUserInitials(message.user)}
                    </Avatar>
                  )}
                  {!isOwnMessage && !isNewSender && (
                    <Box sx={{ width: 32 }} />
                  )}
                  
                  <Box sx={{ maxWidth: '70%' }}>
                    {isNewSender && (
                      <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 1,
                        mb: 0.5,
                        justifyContent: isOwnMessage ? 'flex-end' : 'flex-start'
                      }}>
                        <Typography variant="caption" sx={{ fontWeight: 600 }}>
                          {message.user}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {formatTimestamp(message.timestamp)}
                        </Typography>
                      </Box>
                    )}
                    
                    <Card
                      sx={{
                        p: 1.5,
                        backgroundColor: isOwnMessage ? 'primary.main' : 'background.paper',
                        color: isOwnMessage ? 'white' : 'text.primary',
                        borderRadius: 2,
                        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
                      }}
                    >
                      <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                        {message.message}
                      </Typography>
                    </Card>
                  </Box>
                  
                  {isOwnMessage && isNewSender && (
                    <Avatar 
                      sx={{ 
                        width: 32, 
                        height: 32, 
                        fontSize: '0.8rem',
                        bgcolor: 'primary.main'
                      }}
                    >
                      {getUserInitials(message.user)}
                    </Avatar>
                  )}
                  {isOwnMessage && !isNewSender && (
                    <Box sx={{ width: 32 }} />
                  )}
                </Box>
              );
            })}
            
            {/* Typing indicators */}
            {typingUsers.length > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, pl: 5 }}>
                <Avatar sx={{ width: 24, height: 24, bgcolor: 'grey.400' }}>
                  <Typography variant="caption" sx={{ fontSize: '0.6rem' }}>...</Typography>
                </Avatar>
                <Typography variant="caption" color="text.secondary" fontStyle="italic">
                  {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
                </Typography>
              </Box>
            )}
          </Stack>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Message input */}
      <Box sx={{ 
        p: 2, 
        borderTop: '1px solid #e2e8f0',
        backgroundColor: 'background.paper'
      }}>
        <Box component="form" onSubmit={handleSendMessage}>
          <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
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
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 3,
                  backgroundColor: 'background.paper',
                  '&:hover fieldset': {
                    borderColor: 'primary.main',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: 'primary.main',
                  }
                }
              }}
            />
            <IconButton 
              size="small"
              sx={{ color: 'text.secondary', mb: 0.5 }}
            >
              <EmojiEmotions />
            </IconButton>
            <IconButton 
              size="small"
              sx={{ color: 'text.secondary', mb: 0.5 }}
            >
              <AttachFile />
            </IconButton>
            <IconButton 
              type="submit" 
              disabled={!newMessage.trim()}
              sx={{ 
                bgcolor: 'primary.main',
                color: 'white',
                mb: 0.5,
                '&:hover': {
                  bgcolor: 'primary.dark',
                },
                '&:disabled': {
                  bgcolor: 'grey.300',
                  color: 'grey.500'
                }
              }}
            >
              <SendIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>
      </Box>
    </Card>
  );
};

export default Chat;