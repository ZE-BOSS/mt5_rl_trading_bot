# Automated MT5 Python Trading Bot with Reinforcement Learning

## Overview
This project implements a fully autonomous trading bot that connects to MetaTrader 5 (MT5) using Python. The bot employs a Confluence Breakout Strategy, integrating reinforcement learning for adaptive trading and real-time feedback.

## Features
- **Confluence Breakout Strategy**: Trades are executed based on the alignment of Opening Range Breakout (ORB), Support/Resistance (S/R) tests, and pattern confirmations.
- **Reinforcement Learning**: Utilizes Q-learning or DQN to optimize trading strategies and improve decision-making over time.
- **Dynamic Lot Sizing**: Calculates lot sizes based on account balance and risk parameters.
- **Real-Time Feedback**: Provides verbose logging and feedback during live trading and training sessions.
- **Backtesting**: Comprehensive backtesting capabilities using historical data from MT5.

## Project Structure
```
mt5_rl_trading_bot/
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
├── tests/                      # Unit and integration tests
├── scripts/                    # Utility scripts for data fetching and model training
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── Dockerfile                  # Containerization setup
└── README.md                   # Project documentation
```

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mt5_rl_trading_bot.git
   cd mt5_rl_trading_bot
   ```
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration
- Update the configuration files in the `config/` directory to set your trading parameters, risk management settings, and reinforcement learning hyperparameters.

## Usage
1. Ensure that MetaTrader 5 is installed and configured on your machine.
2. Run the bot:
   ```
   python src/core/bot.py
   ```

## Backtesting
To backtest the trading strategy, use the backtesting engine:
```
python src/backtesting/engine.py
```

## Logging and Monitoring
The bot provides real-time logging of trades and decisions. Logs can be found in the `journals/live_trades/` directory.

## Contribution
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
- Inspired by various trading strategies and reinforcement learning techniques.
- Special thanks to the open-source community for their contributions to trading libraries and frameworks.