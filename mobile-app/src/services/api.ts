import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Change this to your server URL

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface BotConfig {
  symbols: string[];
  risk_per_trade: number;
  max_drawdown: number;
  stop_loss: number;
  take_profit: number;
}

export interface TradeRequest {
  symbol: string;
  action: 'buy' | 'sell';
  volume: number;
  stop_loss?: number;
  take_profit?: number;
}

export interface BacktestRequest {
  symbol: string;
  start_date: string;
  end_date: string;
  episodes?: number;
}

export const apiService = {
  // Bot control
  getBotStatus: () => api.get('/bot/status'),
  startBot: (config?: BotConfig) => api.post('/bot/start', config),
  stopBot: () => api.post('/bot/stop'),
  
  // Configuration
  getBotConfig: () => api.get('/bot/config'),
  updateBotConfig: (config: BotConfig) => api.post('/bot/config', config),
  
  // Trading
  getPositions: () => api.get('/positions'),
  executeTrade: (trade: TradeRequest) => api.post('/trade', trade),
  
  // Market data
  getMarketData: (symbol: string, bars: number = 100) => 
    api.get(`/market-data/${symbol}?bars=${bars}`),
  
  // Backtesting
  runBacktest: (request: BacktestRequest) => api.post('/backtest', request),
  
  // Performance
  getPerformance: () => api.get('/performance'),
};

export default api;