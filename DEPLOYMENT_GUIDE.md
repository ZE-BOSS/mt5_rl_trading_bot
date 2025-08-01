# MT5 Trading Bot System - Deployment Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Complete Trading System                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    WebSocket/REST    ┌─────────────────┐   │
│  │   Mobile App    │ ←──────────────────→ │   FastAPI       │   │
│  │  (React Native) │                      │   Server        │   │
│  └─────────────────┘                      └─────────────────┘   │
│                                                   │             │
│                                                   ▼             │
│                                         ┌─────────────────┐     │
│                                         │   Trading Bot   │     │
│                                         │   (MT5 + RL)    │     │
│                                         └─────────────────┘     │
│                                                   │             │
│                                                   ▼             │
│                                         ┌─────────────────┐     │
│                                         │   MetaTrader 5  │     │
│                                         │   Terminal      │     │
│                                         └─────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Backend Requirements
- Python 3.10+
- MetaTrader 5 Terminal installed
- MT5 account with API access enabled
- Windows/Wine environment (for MT5)

### Frontend Requirements
- Node.js 18+
- Expo CLI
- React Native development environment
- Android Studio / Xcode (for device testing)

## Backend Deployment

### 1. Environment Setup

Create a `.env` file in the root directory:

```env
# MT5 Configuration
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_encrypted_password
MT5_SERVER=your_mt5_server

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Trading Configuration
REINFORCEMENT_LEARNING_ENABLED=True
```

### 2. Docker Deployment (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd mt5-trading-system

# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f trading-bot-api
```

### 3. Manual Deployment

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Start the API server
python api/server.py
```

The API will be available at `http://localhost:8000`

### 4. API Endpoints

#### Bot Control
- `GET /bot/status` - Get bot status
- `POST /bot/start` - Start the trading bot
- `POST /bot/stop` - Stop the trading bot
- `GET /bot/config` - Get bot configuration
- `POST /bot/config` - Update bot configuration

#### Trading
- `GET /positions` - Get open positions
- `POST /trade` - Execute manual trade
- `GET /market-data/{symbol}` - Get market data

#### Analysis
- `POST /backtest` - Run backtest
- `GET /performance` - Get performance metrics

#### WebSocket
- `ws://localhost:8000/ws` - Real-time updates

## Mobile App Deployment

### 1. Setup Development Environment

```bash
# Install Expo CLI
npm install -g @expo/cli

# Navigate to mobile app directory
cd mobile-app

# Install dependencies
npm install
```

### 2. Configuration

Update the API URL in `src/services/api.ts` and `src/context/WebSocketContext.tsx`:

```typescript
const API_BASE_URL = 'http://your-server-ip:8000';
const WS_URL = 'ws://your-server-ip:8000/ws';
```

### 3. Development

```bash
# Start development server
npm start

# Run on Android
npm run android

# Run on iOS
npm run ios
```

### 4. Production Build

```bash
# Build for Android
expo build:android

# Build for iOS
expo build:ios
```

## System Configuration

### 1. Trading Parameters

Edit `config/bot_config.yaml`:

```yaml
symbols:
  - EURUSDm
  - XAUUSDm
  - GBPUSDm

risk_parameters:
  max_drawdown: 10
  risk_per_trade: 0.02
  stop_loss: 50
  take_profit: 100

trading_settings:
  slippage: 3
  leverage: 100
```

### 2. RL Configuration

Edit `config/rl_config.yaml`:

```yaml
learning_rate: 0.001
discount_factor: 0.99
batch_size: 32
memory_size: 100000
```

## Security Considerations

### 1. Password Encryption

Use the secrets manager to encrypt sensitive data:

```python
from src.utils.secrets_manager import SecretsManager
sm = SecretsManager()
encrypted_password = sm.encrypt("your_password")
```

### 2. API Security

- Use HTTPS in production
- Implement authentication tokens
- Rate limiting for API endpoints
- Input validation and sanitization

### 3. Network Security

- Firewall configuration
- VPN for remote access
- Secure WebSocket connections (WSS)

## Monitoring and Logging

### 1. Log Files

- API logs: `journals/api_server.log`
- Trading logs: `journals/trading_bot.log`
- Backtest reports: `journals/backtest_reports/`

### 2. Performance Monitoring

- Real-time P&L tracking
- Trade execution monitoring
- System resource usage
- Error rate monitoring

## Troubleshooting

### Common Issues

1. **MT5 Connection Failed**
   - Verify MT5 terminal is running
   - Check login credentials
   - Ensure API trading is enabled

2. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify server is running
   - Update WebSocket URL in mobile app

3. **Mobile App Not Connecting**
   - Ensure API server is accessible
   - Check network connectivity
   - Verify API URL configuration

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups configured
- [ ] Monitoring alerts set up
- [ ] Error handling tested
- [ ] Performance benchmarks established
- [ ] Security audit completed
- [ ] Documentation updated

## Support and Maintenance

### Regular Tasks

1. **Daily**
   - Check system logs
   - Monitor trading performance
   - Verify MT5 connection

2. **Weekly**
   - Review trading results
   - Update market data
   - Check system resources

3. **Monthly**
   - Backup configuration
   - Update dependencies
   - Performance optimization

### Emergency Procedures

1. **System Failure**
   - Stop all trading immediately
   - Check error logs
   - Restore from backup if needed

2. **Market Events**
   - Monitor high-impact news
   - Adjust risk parameters
   - Manual intervention if required

## Contact Information

For technical support and questions:
- Documentation: See README.md
- Issues: Create GitHub issue
- Emergency: Stop trading immediately and investigate