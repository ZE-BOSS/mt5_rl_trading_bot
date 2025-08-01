"""
Main execution script for MT5 RL Agent
"""

import os
import sys
import logging
import argparse
from datetime import datetime

from src.backtesting.engine import BacktestEngine, fetch_mt5_data, HybridStrategyWrapper
from src.core.bot import TradingBot
from src.core.orb_strategy import OpeningRangeBreakout
from src.core.risk_manager import RiskManager
from src.core.pattern_detector import PatternDetector
from src.core.sr_levels import SupportResistance as SRLevels
from src.reinforcement.agent import DQNAgent
from src.reinforcement.environment import TradingEnvironment
from src.backtesting.optimizer import StrategyOptimizer
import MetaTrader5 as mt5
from src.utils.logger import Logger

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

rl_config = {
    "memory_size": 10000,
    "discount_factor": 0.95,
    "exploration_strategy": {
        "initial_epsilon": 1.0,
        "final_epsilon": 0.01,
        "decay_steps": 500
    },
    "batch_size": 50,
    "update_target_frequency": 10,
    "learning_rate": 0.001,
    "network_architecture": {
        "layers": [128, 128],
        "activation": "relu"
    }
}

logger = Logger('backtest_reports/trading_bot.log')

logger.log('Fetching MT5 account info...')

if not mt5.initialize():
    raise RuntimeError("MT5 initialize() failed")

account_info = mt5.account_info()
account_balance = account_info.balance if account_info is not None else 100
logger.log(f'Account balance set to: {account_balance}')

timeframe = mt5.TIMEFRAME_M15

orb_strategy = OpeningRangeBreakout('07:30', '08:00')
risk_manager = RiskManager(risk_per_trade=0.1, account_balance=account_balance)
pattern_detector = PatternDetector()

def run_backtest(episodes, symbol = 'XAUUSDm'):
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    sr_levels = SRLevels(symbol=symbol, timeframe=timeframe)

    logger.log(f'===== Backtesting trading information from: {start_date} to: {end_date} =====')
    logger.log(f'Fetching MT5 Historical Data for {symbol} on {timeframe}...')
    historical_data = fetch_mt5_data(symbol, timeframe, start_date, end_date)
    logger.log(f'Retrieved {len(historical_data)} historical data points.')

    env = TradingEnvironment(historical_data, initial_balance=account_balance)

    agent = DQNAgent(state_size=env.observation_space.shape[0], action_size=env.action_space.n, config=rl_config)

    from src.reinforcement.trainer import Trainer
    Trainer(agent, env, logger).train(episodes)

    strategy = HybridStrategyWrapper(
        orb_strategy, risk_manager, pattern_detector, sr_levels,
        rl_agent=agent, env=env, historical_data=historical_data, symbol=symbol
    )

    logger.log('Running hybrid backtest...')
    engine = BacktestEngine(strategy, historical_data, account_balance, risk_manager, agent, env, symbol)
    engine.run_backtest()
    report = engine.generate_report()
    print(report)

    engine._plot_equity_curve()

    logger.log('Starting strategy optimization...')

    strategy_optimizer = StrategyOptimizer(
        historical_data=historical_data,
        symbol=symbol,
        timeframe=timeframe,
        account_balance=account_balance,
        logger=logger
    )

    parameter_grid = {
        'start_time': ['07:00', '08:00'],
        'end_time': ['07:30', '08:30'],
        'risk': [0.01, 0.02]
    }

    best_params = strategy_optimizer.optimize(parameter_grid, metric="sharpe")
    logger.log(f"Best parameters: {best_params}")

    engine._plot_equity_curve()

def run_live():
    bot = TradingBot()
    bot.run()

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='MT5 Reinforcement Learning Agent')
    parser.add_argument('--mode', choices=['backtest', 'live'], 
                       default='backtest', help='Operation mode')
    parser.add_argument('--symbols', default='XAUUSDm', choices=['EURUSDm', 'GBPUSDm', 'XAUUSDm', 'GBPJPYm', 'XAGUSDm', 'US30', 'NAS100', 'BTCUSDm', 'ETHUSDm', 'USDJPYm'], 
                       help='Trading symbols')
    parser.add_argument('--episodes', type=int, default=100, 
                       help='Training episodes')

    args = parser.parse_args()

    try:
        if args.mode == 'backtest':
            run_backtest(args.episodes, args.symbols)
        elif args.mode == 'live':
            run_live()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logging.error(f"Error in main execution: {e}")

if __name__ == '__main__':
    main()
