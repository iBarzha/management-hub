class WebSocketService {
  constructor() {
    this.connections = new Map();
    this.messageHandlers = new Map();
    this.isConnecting = new Map();
  }

  connect(url, room, token) {
    const connectionKey = `${url}_${room}`;
    
    if (this.connections.has(connectionKey)) {
      return this.connections.get(connectionKey);
    }

    if (this.isConnecting.get(connectionKey)) {
      return null;
    }

    this.isConnecting.set(connectionKey, true);

    const wsUrl = `ws://localhost:8000${url}${room}/?token=${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log(`WebSocket connected to ${room}`);
      this.isConnecting.set(connectionKey, false);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(connectionKey, data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error, event.data);
      }
    };

    ws.onclose = (event) => {
      console.log(`WebSocket disconnected from ${room}:`, event.code, event.reason);
      this.connections.delete(connectionKey);
      this.isConnecting.set(connectionKey, false);
      
      // Attempt to reconnect after 3 seconds
      if (event.code !== 1000) {
        setTimeout(() => {
          this.connect(url, room, token);
        }, 3000);
      }
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error for ${room}:`, error);
      this.isConnecting.set(connectionKey, false);
    };

    this.connections.set(connectionKey, ws);
    return ws;
  }

  disconnect(url, room) {
    const connectionKey = `${url}_${room}`;
    const ws = this.connections.get(connectionKey);
    
    if (ws) {
      ws.close(1000, 'Intentional disconnect');
      this.connections.delete(connectionKey);
      this.messageHandlers.delete(connectionKey);
    }
  }

  sendMessage(url, room, message) {
    const connectionKey = `${url}_${room}`;
    const ws = this.connections.get(connectionKey);
    
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    } else {
      console.error(`WebSocket not connected for ${room}`);
    }
  }

  addMessageHandler(url, room, handler) {
    const connectionKey = `${url}_${room}`;
    if (!this.messageHandlers.has(connectionKey)) {
      this.messageHandlers.set(connectionKey, []);
    }
    this.messageHandlers.get(connectionKey).push(handler);
  }

  removeMessageHandler(url, room, handler) {
    const connectionKey = `${url}_${room}`;
    const handlers = this.messageHandlers.get(connectionKey);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  handleMessage(connectionKey, data) {
    const handlers = this.messageHandlers.get(connectionKey) || [];
    handlers.forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
  }

  // Chat-specific methods
  connectToChat(room, token) {
    return this.connect('/ws/chat/', room, token);
  }

  connectToNotifications(userId, token) {
    return this.connect('/ws/notifications/', userId, token);
  }

  connectToProject(projectId, token) {
    return this.connect('/ws/project/', projectId, token);
  }

  sendChatMessage(room, message) {
    this.sendMessage('/ws/chat/', room, {
      type: 'chat_message',
      message: message
    });
  }

  sendTypingIndicator(room, isTyping) {
    this.sendMessage('/ws/chat/', room, {
      type: 'typing',
      is_typing: isTyping
    });
  }

  sendTaskUpdate(projectId, taskId, updates) {
    this.sendMessage('/ws/project/', projectId, {
      type: 'task_update',
      task_id: taskId,
      updates: updates,
      timestamp: new Date().toISOString()
    });
  }

  disconnectAll() {
    this.connections.forEach((ws, key) => {
      ws.close(1000, 'Disconnecting all');
    });
    this.connections.clear();
    this.messageHandlers.clear();
    this.isConnecting.clear();
  }
}

const webSocketService = new WebSocketService();
export default webSocketService;