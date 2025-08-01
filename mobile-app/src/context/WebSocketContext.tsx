import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { showMessage } from 'react-native-flash-message';

interface WebSocketContextType {
  isConnected: boolean;
  botStatus: any;
  positions: any[];
  marketData: any;
  sendMessage: (message: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [botStatus, setBotStatus] = useState({
    running: false,
    connected: false,
    error: null
  });
  const [positions, setPositions] = useState([]);
  const [marketData, setMarketData] = useState({});

  const WS_URL = 'ws://localhost:8000/ws'; // Change this to your server URL

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        showMessage({
          message: 'Connected to trading server',
          type: 'success',
          duration: 2000,
        });
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        showMessage({
          message: 'Disconnected from trading server',
          type: 'warning',
          duration: 2000,
        });
        
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          connectWebSocket();
        }, 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        showMessage({
          message: 'Connection error',
          type: 'danger',
          duration: 3000,
        });
      };

      setSocket(ws);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      showMessage({
        message: 'Failed to connect to server',
        type: 'danger',
        duration: 3000,
      });
    }
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'bot_status':
        setBotStatus(data.data);
        break;
      case 'positions_update':
        setPositions(data.data);
        break;
      case 'market_data':
        setMarketData(prev => ({
          ...prev,
          [data.symbol]: data.data
        }));
        break;
      case 'trade_executed':
        showMessage({
          message: `Trade executed: ${data.data.action.toUpperCase()} ${data.data.volume} ${data.data.symbol}`,
          type: 'success',
          duration: 4000,
        });
        break;
      case 'error':
        showMessage({
          message: data.message || 'An error occurred',
          type: 'danger',
          duration: 4000,
        });
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const sendMessage = (message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    } else {
      showMessage({
        message: 'Not connected to server',
        type: 'warning',
        duration: 2000,
      });
    }
  };

  return (
    <WebSocketContext.Provider
      value={{
        isConnected,
        botStatus,
        positions,
        marketData,
        sendMessage,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};