import pandas as pd

class ORBStrategyWrapper:
    """
    Wraps OpeningRangeBreakout and dependencies for backtesting with historical data.
    """
    def __init__(self, orb_strategy, risk_manager, pattern_detector, sr_levels):
        self.orb_strategy = orb_strategy
        self.risk_manager = risk_manager
        self.pattern_detector = pattern_detector
        self.sr_levels = sr_levels
        self.last_entry_signal = None

    def should_enter(self, row):
        # Simulate fetching S/R and patterns from historical row
        s_r_levels = self.sr_levels.get_sr_levels(row)
        patterns = self.pattern_detector.analyze_patterns(pd.DataFrame([row]))
        if self.orb_strategy.is_setup_valid(row, s_r_levels, patterns):
            self.last_entry_signal = self.orb_strategy.get_entry_signal(row)
            return True
        return False

    def should_exit(self, row):
        # You can add exit logic based on your strategy
        return self.orb_strategy.should_exit(row)

    def calculate_position_size(self, entry_price):
        return self.risk_manager.calculate_lot_size(self.last_entry_signal)
    
def fetch_mt5_data(symbol, timeframe, start_date, end_date):
    """
    Fetch historical OHLCV data from MetaTrader5 and return as a pandas DataFrame.
    """
    import MetaTrader5 as mt5
    import pandas as pd
    if not mt5.initialize():
        raise RuntimeError("MT5 initialize() failed")
    rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
    mt5.shutdown()
    if rates is None:
        raise RuntimeError(f"Failed to fetch data for {symbol}")
    df = pd.DataFrame(rates)
    df.rename(columns={
        'time': 'Time', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'tick_volume': 'Volume'
    }, inplace=True)
    df['Time'] = pd.to_datetime(df['Time'], unit='s')
    return df

class RLStrategyWrapper:
    """
    Wraps an RL agent to provide should_enter, should_exit, and calculate_position_size for backtesting.
    """
    def __init__(self, rl_agent, env):
        self.rl_agent = rl_agent
        self.env = env
        self.last_action = 0
        self.position_size = 1

    def should_enter(self, row):
        # Use RL agent to decide action
        state = self.env._get_observation_from_row(row)
        action = self.rl_agent.choose_action(state)
        self.last_action = action
        return action == 1  # 1 = buy

    def should_exit(self, row):
        # Use RL agent to decide action
        state = self.env._get_observation_from_row(row)
        action = self.rl_agent.choose_action(state)
        return action == 2  # 2 = sell

    def calculate_position_size(self, entry_price):
        return self.position_size

def run_rl_backtest_and_train(rl_agent, env, historical_data, episodes=100):
    """
    Automates RL agent training and backtesting using the RLStrategyWrapper.
    """
    # Train RL agent
    from src.reinforcement.trainer import Trainer
    from src.utils.logger import Logger
    logger = Logger()
    trainer = Trainer(rl_agent, env, logger)
    trainer.train(episodes)

    # Backtest RL agent
    strategy = RLStrategyWrapper(rl_agent, env)
    engine = BacktestEngine(strategy, historical_data)
    engine.run_backtest()
    report = engine.generate_report()
    logger.log("Backtest complete. Report:")
    logger.log(report)
    return report
from datetime import datetime
import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self, strategy, historical_data):
        self.strategy = strategy
        self.historical_data = historical_data
        self.results = []

    def run_backtest(self):
        for index, row in self.historical_data.iterrows():
            if self.strategy.should_enter(row):
                entry_price = row['Close']
                position_size = self.strategy.calculate_position_size(entry_price)
                self.execute_trade(entry_price, position_size)

            if self.strategy.should_exit(row):
                exit_price = row['Close']
                self.close_trade(exit_price)

    def execute_trade(self, entry_price, position_size):
        trade = {
            'entry_time': datetime.now(),
            'entry_price': entry_price,
            'position_size': position_size,
            'exit_price': None,
            'outcome': None
        }
        self.results.append(trade)

    def close_trade(self, exit_price):
        if self.results:
            trade = self.results[-1]
            trade['exit_price'] = exit_price
            trade['outcome'] = (exit_price - trade['entry_price']) * trade['position_size']
            trade['exit_time'] = datetime.now()

    def generate_report(self):
        report = pd.DataFrame(self.results)
        report['profit_loss'] = report['outcome'].cumsum()
        return report

    def optimize_strategy(self, param_grid):
        best_strategy = None
        best_performance = -np.inf

        for params in param_grid:
            self.strategy.set_parameters(params)
            self.run_backtest()
            performance = self.evaluate_performance()

            if performance > best_performance:
                best_performance = performance
                best_strategy = self.strategy

        return best_strategy

    def evaluate_performance(self):
        total_profit = sum(trade['outcome'] for trade in self.results if trade['outcome'] is not None)
        return total_profit / len(self.results) if self.results else 0.0


# Standalone backtest runner
if __name__ == "__main__":
    import pandas as pd
    from src.core.orb_strategy import OpeningRangeBreakout
    from src.core.risk_manager import RiskManager
    from src.core.pattern_detector import PatternDetector
    from src.core.sr_levels import SupportResistance as SRLevels
    import MetaTrader5 as mt5
    from datetime import datetime
    
    symbol = 'EURUSDm'
    timeframe = mt5.TIMEFRAME_M15
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    historical_data = fetch_mt5_data(symbol, timeframe, start_date, end_date)
    orb_strategy = OpeningRangeBreakout('07:00', '07:30')
    account_info = mt5.account_info()
    account_balance = account_info.balance if account_info is not None else 10000  # fallback to 10k if not available
    risk_manager = RiskManager(risk_per_trade=0.02, account_balance=account_balance)
    pattern_detector = PatternDetector()
    sr_levels = SRLevels(symbol=symbol, timeframe=timeframe)
    strategy = ORBStrategyWrapper(orb_strategy, risk_manager, pattern_detector, sr_levels)
    engine = BacktestEngine(strategy, historical_data)
    engine.run_backtest()
    report = engine.generate_report()
    print(report)

    from src.backtesting.optimizer import StrategyOptimizer
    parameter_grid = {
        'start_time': ['07:00', '08:00'],
        'end_time': ['07:30', '08:30'],
        'risk': [0.01, 0.02]
    }

    strategy_optimizer = StrategyOptimizer(historical_data)
    best_params = strategy_optimizer.optimize(parameter_grid)
    print(f"Best strategy params: {best_params}")