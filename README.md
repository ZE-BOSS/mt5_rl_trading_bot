# Complete MT5 Trading System with Mobile App

## Overview
This project implements a comprehensive trading system with a Python-based MT5 trading bot backend and a React Native mobile application frontend. The system features real-time communication, advanced RL-based trading strategies, and a modern mobile interface for complete trading control.

## Features

### Backend Features
- **Advanced Trading Bot**: MT5 integration with RL-powered decision making
- **Confluence Breakout Strategy**: ORB, S/R levels, and pattern confirmations
- **Reinforcement Learning**: DQN agent for adaptive trading strategies
- **FastAPI Server**: RESTful API with WebSocket support for real-time updates
- **Comprehensive Backtesting**: Historical testing with performance optimization
- **Risk Management**: Dynamic lot sizing and drawdown protection

### Frontend Features
- **React Native Mobile App**: Cross-platform iOS/Android application
- **Real-time Dashboard**: Live P&L, positions, and market data visualization
- **Trading Controls**: Start/stop bot, manual trading, parameter adjustment
- **Performance Analytics**: Interactive charts and comprehensive metrics
- **WebSocket Integration**: Real-time updates and notifications

## Project Structure
```
mt5-trading-system/
├── backend/                    # FastAPI server and trading logic
│   ├── api/                    # REST API and WebSocket endpoints
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile             # Backend containerization
├── mobile-app/                # React Native mobile application
│   ├── src/                   # Mobile app source code
│   │   ├── screens/           # App screens (Dashboard, Trading, etc.)
│   │   ├── services/          # API integration
│   │   └── context/           # WebSocket and state management
│   ├── package.json           # Node.js dependencies
│   └── app.json              # Expo configuration
├── config/                     # Configuration files for bot settings and RL parameters
├── src/                        # Source code for the trading bot
│   ├── core/                   # Core functionalities of the bot
│   ├── reinforcement/          # Reinforcement learning components
│   ├── utils/                  # Utility functions and logging
│   ├── backtesting/            # Backtesting logic and optimization
│   └── integration/            # Integration with external services
├── data/                       # Data storage for historical and live data
├── models/                     # Trained RL models
├── journals/                   # Trade logs and backtest reports
├── docker-compose.yml          # Multi-service deployment
├── DEPLOYMENT_GUIDE.md         # Comprehensive deployment instructions
├── API_DOCUMENTATION.md        # Complete API reference
└── SYSTEM_ANALYSIS.md          # Technical analysis and architecture
```

## Quick Start

### 1. Backend Setup
```bash
# Using Docker (Recommended)
docker-compose up -d

# Or manual setup
cd backend
pip install -r requirements.txt
python api/server.py
```

### 2. Mobile App Setup
```bash
cd mobile-app
npm install
npm start
```

### 3. Configuration
Create `.env` file with your MT5 credentials:
```env
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server
```

## System Architecture

```
┌─────────────────┐    WebSocket/REST    ┌─────────────────┐
│   Mobile App    │ ←──────────────────→ │   FastAPI       │
│  (React Native) │                      │   Server        │
└─────────────────┘                      └─────────────────┘
                                                   │
                                                   ▼
                                         ┌─────────────────┐
                                         │   Trading Bot   │
                                         │   (MT5 + RL)    │
                                         └─────────────────┘
                                                   │
                                                   ▼
                                         ┌─────────────────┐
                                         │   MetaTrader 5  │
                                         │   Terminal      │
                                         └─────────────────┘
```

## Key Components

### Backend API Endpoints
- **Bot Control**: `/bot/start`, `/bot/stop`, `/bot/status`
- **Trading**: `/trade`, `/positions`, `/market-data/{symbol}`
- **Analysis**: `/backtest`, `/performance`
- **WebSocket**: Real-time updates at `/ws`

### Mobile App Features
- **Dashboard**: Real-time P&L, bot status, performance metrics
- **Trading Screen**: Manual trading, market data, bot controls
- **Positions**: Live position monitoring and management
- **Backtesting**: Historical strategy testing with visualization
- **Settings**: Configuration management and system controls

## Advanced Features

### Reinforcement Learning
- **DQN Agent**: Deep Q-Network for trading decisions
- **Experience Replay**: Prioritized replay buffer for training
- **Adaptive Learning**: Continuous strategy optimization
- **Multi-timeframe Analysis**: Complex state representation

### Risk Management
- **Dynamic Position Sizing**: Account balance-based lot calculation
- **Drawdown Protection**: Maximum loss limits
- **Stop Loss/Take Profit**: Automated risk controls
- **Portfolio Diversification**: Multi-symbol trading support

### Real-time Communication
- **WebSocket Streaming**: Live market data and trade updates
- **Push Notifications**: Trade alerts and system status
- **Error Handling**: Robust connection management
- **Data Synchronization**: Consistent state across platforms

## Performance Monitoring

### Metrics Tracked
- Win rate and profit factor
- Maximum drawdown
- Sharpe ratio
- Trade frequency and duration
- System resource usage

### Visualization
- Equity curve charts
- Performance heatmaps
- Trade distribution analysis
- Real-time P&L tracking

## Security Features

- **Password Encryption**: Secure credential storage
- **API Rate Limiting**: Protection against abuse
- **Input Validation**: Comprehensive data sanitization
- **Error Handling**: Graceful failure management

## Documentation

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)**: Complete setup instructions
- **[API Documentation](API_DOCUMENTATION.md)**: Comprehensive API reference
- **[System Analysis](SYSTEM_ANALYSIS.md)**: Technical architecture details

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
python api/server.py
```

### Mobile Development
```bash
cd mobile-app
npm install
npm start
# Then press 'a' for Android or 'i' for iOS
```

### Testing
```bash
# Backend tests
cd backend
python -m pytest

# API testing
http GET localhost:8000/bot/status
```

## Production Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Manual Deployment
1. Configure environment variables
2. Install dependencies
3. Start API server
4. Build mobile app
5. Configure reverse proxy (nginx)
6. Set up monitoring and logging

## Troubleshooting

### Common Issues
1. **MT5 Connection**: Ensure terminal is running and API is enabled
2. **WebSocket Issues**: Check firewall and network connectivity
3. **Mobile App**: Verify API URL configuration
4. **Performance**: Monitor system resources and optimize parameters

### Debug Mode
Enable detailed logging for troubleshooting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contribution
Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
- MetaTrader 5 API for trading integration
- TensorFlow for machine learning capabilities
- React Native and Expo for mobile development
- FastAPI for high-performance API development
- Open-source trading and ML communities

## Support

For support and questions:
- Check the documentation files
- Review the troubleshooting section
- Create an issue on GitHub
- Follow the deployment guide for setup help

---

**⚠️ Risk Disclaimer**: Trading involves substantial risk of loss. This software is for educational and research purposes. Always test thoroughly before using with real money.