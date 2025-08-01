# MT5 Trading Bot API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API does not require authentication. In production, implement proper authentication mechanisms.

## WebSocket Connection
```
ws://localhost:8000/ws
```

## REST API Endpoints

### Bot Management

#### Get Bot Status
```http
GET /bot/status
```

**Response:**
```json
{
  "running": false,
  "connected": false,
  "error": null
}
```

#### Start Bot
```http
POST /bot/start
```

**Request Body (Optional):**
```json
{
  "symbols": ["EURUSDm", "XAUUSDm"],
  "risk_per_trade": 0.02,
  "max_drawdown": 0.1,
  "stop_loss": 50,
  "take_profit": 100
}
```

**Response:**
```json
{
  "message": "Bot started successfully",
  "status": {
    "running": true,
    "connected": true,
    "error": null
  }
}
```

#### Stop Bot
```http
POST /bot/stop
```

**Response:**
```json
{
  "message": "Bot stopped successfully",
  "status": {
    "running": false,
    "connected": false,
    "error": null
  }
}
```

### Configuration Management

#### Get Bot Configuration
```http
GET /bot/config
```

**Response:**
```json
{
  "symbols": ["EURUSDm", "XAUUSDm"],
  "risk_parameters": {
    "risk_per_trade": 0.02,
    "max_drawdown": 0.1,
    "stop_loss": 50,
    "take_profit": 100
  },
  "trading_settings": {
    "slippage": 3,
    "leverage": 100
  }
}
```

#### Update Bot Configuration
```http
POST /bot/config
```

**Request Body:**
```json
{
  "symbols": ["EURUSDm", "XAUUSDm"],
  "risk_per_trade": 0.02,
  "max_drawdown": 0.1,
  "stop_loss": 50,
  "take_profit": 100
}
```

### Trading Operations

#### Get Open Positions
```http
GET /positions
```

**Response:**
```json
{
  "positions": [
    {
      "ticket": 123456789,
      "symbol": "EURUSDm",
      "type": "buy",
      "volume": 0.01,
      "price_open": 1.1000,
      "price_current": 1.1050,
      "profit": 5.00,
      "sl": 1.0950,
      "tp": 1.1100
    }
  ]
}
```

#### Execute Manual Trade
```http
POST /trade
```

**Request Body:**
```json
{
  "symbol": "EURUSDm",
  "action": "buy",
  "volume": 0.01,
  "stop_loss": 1.0950,
  "take_profit": 1.1100
}
```

**Response:**
```json
{
  "message": "Trade executed successfully",
  "result": {
    "ticket": 123456789,
    "symbol": "EURUSDm",
    "action": "buy",
    "volume": 0.01,
    "price": 1.1000
  }
}
```

### Market Data

#### Get Market Data
```http
GET /market-data/{symbol}?bars=100
```

**Parameters:**
- `symbol`: Trading symbol (e.g., EURUSDm)
- `bars`: Number of bars to retrieve (default: 100)

**Response:**
```json
{
  "symbol": "EURUSDm",
  "data": [
    {
      "time": "2024-01-01T00:00:00",
      "open": 1.1000,
      "high": 1.1050,
      "low": 1.0950,
      "close": 1.1025,
      "tick_volume": 1000
    }
  ]
}
```

### Backtesting

#### Run Backtest
```http
POST /backtest
```

**Request Body:**
```json
{
  "symbol": "XAUUSDm",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "episodes": 100
}
```

**Response:**
```json
{
  "symbol": "XAUUSDm",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "results": [
    {
      "entry_time": "2024-01-01T08:00:00",
      "entry_price": 2000.00,
      "exit_time": "2024-01-01T10:00:00",
      "exit_price": 2010.00,
      "outcome": 100.00,
      "balance_after": 10100.00
    }
  ],
  "summary": {
    "total_trades": 50,
    "final_balance": 11500.00,
    "total_return": 1500.00,
    "max_drawdown": 200.00
  }
}
```

### Performance Metrics

#### Get Performance Data
```http
GET /performance
```

**Response:**
```json
{
  "total_trades": 100,
  "winning_trades": 65,
  "losing_trades": 35,
  "win_rate": 0.65,
  "total_profit": 1500.00,
  "max_drawdown": 200.00,
  "sharpe_ratio": 1.25,
  "last_updated": "2024-01-01T12:00:00"
}
```

## WebSocket Messages

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Message Types

#### Bot Status Update
```json
{
  "type": "bot_status",
  "data": {
    "running": true,
    "connected": true,
    "error": null
  }
}
```

#### Trade Executed
```json
{
  "type": "trade_executed",
  "data": {
    "symbol": "EURUSDm",
    "action": "buy",
    "volume": 0.01,
    "price": 1.1000,
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

#### Positions Update
```json
{
  "type": "positions_update",
  "data": [
    {
      "ticket": 123456789,
      "symbol": "EURUSDm",
      "type": "buy",
      "volume": 0.01,
      "profit": 5.00
    }
  ]
}
```

#### Market Data Update
```json
{
  "type": "market_data",
  "symbol": "EURUSDm",
  "data": {
    "time": "2024-01-01T12:00:00",
    "bid": 1.1000,
    "ask": 1.1002,
    "last": 1.1001
  }
}
```

#### Error Message
```json
{
  "type": "error",
  "message": "Connection to MT5 failed",
  "timestamp": "2024-01-01T12:00:00"
}
```

## Error Handling

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

### Error Response Format
```json
{
  "detail": "Error message description"
}
```

### Common Errors

#### Bot Not Initialized
```json
{
  "detail": "Bot not initialized"
}
```

#### MT5 Connection Failed
```json
{
  "detail": "Failed to connect to MT5"
}
```

#### Invalid Parameters
```json
{
  "detail": "Please enter a valid volume"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing:
- Request rate limits per IP
- WebSocket connection limits
- Trade execution throttling

## Data Models

### BotConfig
```typescript
interface BotConfig {
  symbols: string[];
  risk_per_trade: number;
  max_drawdown: number;
  stop_loss: number;
  take_profit: number;
}
```

### TradeRequest
```typescript
interface TradeRequest {
  symbol: string;
  action: 'buy' | 'sell';
  volume: number;
  stop_loss?: number;
  take_profit?: number;
}
```

### Position
```typescript
interface Position {
  ticket: number;
  symbol: string;
  type: 'buy' | 'sell';
  volume: number;
  price_open: number;
  price_current: number;
  profit: number;
  sl: number;
  tp: number;
}
```

### BacktestRequest
```typescript
interface BacktestRequest {
  symbol: string;
  start_date: string;
  end_date: string;
  episodes?: number;
}
```

## SDK Examples

### JavaScript/TypeScript
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Start bot
const startBot = async () => {
  const response = await api.post('/bot/start');
  return response.data;
};

// Get positions
const getPositions = async () => {
  const response = await api.get('/positions');
  return response.data.positions;
};

// Execute trade
const executeTrade = async (trade: TradeRequest) => {
  const response = await api.post('/trade', trade);
  return response.data;
};
```

### Python
```python
import requests
import websocket

# REST API
api_base = "http://localhost:8000"

def start_bot():
    response = requests.post(f"{api_base}/bot/start")
    return response.json()

def get_positions():
    response = requests.get(f"{api_base}/positions")
    return response.json()["positions"]

# WebSocket
def on_message(ws, message):
    data = json.loads(message)
    print(f"Received: {data}")

ws = websocket.WebSocketApp("ws://localhost:8000/ws",
                          on_message=on_message)
ws.run_forever()
```

## Testing

### Unit Tests
```bash
cd backend
python -m pytest tests/
```

### API Testing
```bash
# Install httpie
pip install httpie

# Test endpoints
http GET localhost:8000/bot/status
http POST localhost:8000/bot/start
http GET localhost:8000/positions
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8000
```