# WebSocket API Documentation

## Enhanced MT5 Trading Bot Real-time Monitoring

### Connection
- **URL**: `ws://localhost:8000/ws`
- **Protocol**: WebSocket
- **Auto-reconnection**: Yes (with exponential backoff)

### Message Types

#### Client to Server Messages

##### 1. Ping Message
```json
{
  "type": "ping"
}
```
**Response**: `{"type": "pong"}`

##### 2. Status Request
```json
{
  "type": "request_status"
}
```
**Response**: Current bot status object

#### Server to Client Messages

##### 1. Connection Established
```json
{
  "type": "connection_established",
  "connection_id": "uuid",
  "bot_status": {
    "running": false,
    "connected": false,
    "error": null,
    "trades_this_week": 0,
    "last_trade_time": null
  }
}
```

##### 2. Real-time Log Events
All log events follow this structure:
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "session_id": "uuid",
  "event_type": "EVENT_TYPE",
  "level": "INFO|ERROR|DEBUG",
  "data": { /* event-specific data */ }
}
```

### Event Types

#### BOT_INITIALIZATION
```json
{
  "event_type": "BOT_INITIALIZATION",
  "data": {
    "config": {
      "symbols": ["EURUSDm", "XAUUSDm"],
      "risk_parameters": { /* risk config */ },
      "trading_settings": { /* trading config */ }
    },
    "rl_enabled": true,
    "mt5_connected": true
  }
}
```

#### TRADE_ENTRY
```json
{
  "event_type": "TRADE_ENTRY",
  "data": {
    "symbol": "EURUSDm",
    "direction": "buy",
    "price": 1.1234,
    "lot_size": 0.1,
    "stop_loss": 1.1200,
    "take_profit": 1.1300,
    "patterns_detected": ["Bullish Engulfing"],
    "sr_levels": {"support": 1.1200, "resistance": 1.1300},
    "aggression_multiplier": 1.0,
    "trades_this_week": 3,
    "execution_result": { /* MT5 execution result */ }
  }
}
```

#### TRADE_EXIT
```json
{
  "event_type": "TRADE_EXIT",
  "data": {
    "symbol": "EURUSDm",
    "exit_price": 1.1250,
    "exit_reason": "Take profit hit",
    "pnl": 150.0,
    "balance_after": 10150.0,
    "timestamp": "2024-01-15T10:35:00"
  }
}
```

#### DECISION
```json
{
  "event_type": "DECISION",
  "data": {
    "symbol": "EURUSDm",
    "decision": "skip_max_trades_reached|increase_aggression|rl_action",
    "reason": "Detailed reasoning",
    "trades_this_week": 10,
    "max_trades": 10,
    "aggression_multiplier": 1.5
  }
}
```

#### ERROR
```json
{
  "event_type": "ERROR",
  "data": {
    "error": "Error message",
    "traceback": "Full stack trace",
    "symbol": "EURUSDm" // if applicable
  }
}
```

#### PERFORMANCE
```json
{
  "event_type": "PERFORMANCE",
  "data": {
    "total_trades": 25,
    "win_rate": 0.65,
    "total_profit": 1250.0,
    "max_drawdown": 0.08,
    "weekly_target": {
      "min_trades": 3,
      "max_trades": 10,
      "current_trades": 5
    }
  }
}
```

#### BACKTEST Events

##### BACKTEST_START
```json
{
  "event_type": "BACKTEST_START",
  "data": {
    "session_id": "uuid",
    "symbol": "EURUSDm",
    "data_points": 10000,
    "starting_balance": 10000,
    "trade_constraints": {
      "min_trades_per_week": 3,
      "max_trades_per_week": 10
    }
  }
}
```

##### WEEKLY_SUMMARY
```json
{
  "event_type": "WEEKLY_SUMMARY",
  "data": {
    "week": 3,
    "trades": 5,
    "target_range": "3-10",
    "balance": 10250.0,
    "within_target": true
  }
}
```

##### BACKTEST_COMPLETE
```json
{
  "event_type": "BACKTEST_COMPLETE",
  "data": {
    "session_id": "uuid",
    "final_balance": 12500.0,
    "total_return": 2500.0,
    "total_trades": 45,
    "max_drawdown": 850.0,
    "weekly_stats": {
      "1": {"trades": 4, "within_target": true},
      "2": {"trades": 6, "within_target": true}
    }
  }
}
```

### Trade Frequency Constraints

The system enforces the following constraints:

- **Minimum trades per week**: 3 (configurable)
- **Maximum trades per week**: 10 (configurable)
- **Aggression adjustment**: Position sizes increase by 30% when under minimum
- **Trade blocking**: No new trades when maximum reached

### Error Handling

- **Connection drops**: Automatic reconnection with exponential backoff
- **Message parsing errors**: Logged but don't break connection
- **Rate limiting**: Built-in message throttling to prevent spam

### Frontend Integration

The frontend automatically:
- Connects to WebSocket on page load
- Handles reconnection on connection loss
- Updates UI based on real-time events
- Maintains scrollable log with 1000 entry limit
- Provides manual controls for bot operations

### Security Considerations

- No authentication required for local development
- All sensitive data (passwords, API keys) handled server-side
- WebSocket messages are JSON-formatted and validated
- Rate limiting prevents message flooding