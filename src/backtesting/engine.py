import pandas as pd
from src.utils.logger import Logger
import matplotlib.pyplot as plt

logger = Logger('backtest_reports/trading_bot.log')

class HybridStrategyWrapper:
    def __init__(self, orb_strategy, risk_manager, pattern_detector, sr_levels, rl_agent, env, historical_data, symbol):
        self.orb_strategy = orb_strategy
        self.risk_manager = risk_manager
        self.pattern_detector = pattern_detector
        self.sr_levels = sr_levels
        self.rl_agent = rl_agent
        self.env = env
        self.historical_data = historical_data
        self.in_trade = False
        self.last_entry_signal = None
        self.last_action = 0
        self.symbol = symbol

    def should_enter(self, row):
        i = row.name
        s_r_levels = self.sr_levels.get_sr_levels(row)
        patterns = []

        if i >= 2:
            window = self.historical_data.iloc[i - 2:i + 1]
            patterns = self.pattern_detector.analyze_patterns(window)

        if not self.orb_strategy.is_setup_valid(row, s_r_levels, patterns):
            return False

        signal = self.orb_strategy.get_entry_signal(row)
        if not signal:
            return False

        state = self.env._get_observation_from_row(row)
        action = self.rl_agent.select_action(state)

        if action == 1:
            self.last_entry_signal = signal
            self.orb_strategy.entry_price = signal["price"]
            self.orb_strategy.stop_loss_price = signal["stop_loss"]
            self.orb_strategy.entry_time = row["Time"]
            self.orb_strategy.current_trade = "long" if signal["direction"] == "buy" else "short"
            self.in_trade = True
            return True

        return False

    def should_exit(self, row):
        if not self.in_trade or not self.last_entry_signal:
            return False

        state = self.env._get_observation_from_row(row)
        action = self.rl_agent.select_action(state)

        if action == 2:
            self.in_trade = False
            return {
                "exit_price": row['Close'],
                "reason": "RL exit"
            }

        return False

    def calculate_position_size(self, entry_price):
        if self.last_entry_signal is None:
            return 0
        return self.risk_manager.calculate_lot_size(self.last_entry_signal, self.symbol)

class BacktestEngine:
    def __init__(self, strategy, historical_data, starting_balance, risk_manager, agent, env, symbol):
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.historical_data = historical_data
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.agent = agent
        self.env = env
        self.equity_curve = []
        self.results = []
        self.in_trade = False
        self.max_drawdown = 0
        self.peak_balance = starting_balance
        self.symbol = symbol

    def run_backtest(self):
        trade_count = 0
        max_trades = 10
        min_trades = 3
        trades_this_week = 0
        current_week = None

        for index, row in self.historical_data.iterrows():
            row_week = row['Time'].isocalendar().week

            if current_week is None:
                current_week = row_week

            if row_week != current_week:
                if trades_this_week < min_trades:
                    logger.log(f"⚠️ Agent took only {trades_this_week} trades in week {current_week}. Encourage more trades.")
                current_week = row_week
                trades_this_week = 0

            if self.balance <= 0:
                logger.log("❌ Account balance depleted or zero. Ending backtest early and resetting agent's rewards.")
                self.env.balance = 0  # Simulate real environment balance collapse
                self.agent.memory.buffer.clear()  # Clear experience memory for this episode
                self.equity_curve.append(self.balance)
                break

            if trade_count >= max_trades:
                logger.log("✅ Maximum number of trades reached. Ending backtest.")
                break

            if not self.in_trade and self.strategy.should_enter(row):
                entry_price = row['Close']
                position_size = self.strategy.calculate_position_size(entry_price)
                self.execute_trade(entry_price, position_size, row)
                logger.log(f'Trade({index}) entered at: {entry_price}, with lot size: {position_size}')
                self.in_trade = True
                trade_count += 1
                trades_this_week += 1

            if self.in_trade:
                exit_signal = self.strategy.should_exit(row)
                if isinstance(exit_signal, dict):
                    exit_price = exit_signal.get("exit_price", row['Close'])
                    self.close_trade(exit_price, row)
                    logger.log(f'Trade exited at: {exit_price}')
                    self.in_trade = False

            self.equity_curve.append(self.balance)

        if not self.results:
            logger.log("⚠️ No trades were executed or retained during this backtest.")

    def execute_trade(self, entry_price, position_size, row):
        trade = {
            'entry_time': row['Time'],
            'entry_price': entry_price,
            'position_size': position_size,
            'exit_price': None,
            'exit_time': None,
            'outcome': None,
            'balance_before': self.balance
        }
        self.results.append(trade)

    def close_trade(self, exit_price, row):
        if self.results:
            trade = self.results[-1]
            trade['exit_price'] = exit_price
            trade['exit_time'] = row['Time']

            price_diff = exit_price - trade['entry_price']
            pip_multiplier, contract_size = self.risk_manager._get_multiplier_and_contract(self.symbol)
            pip_diff = price_diff * pip_multiplier
            pip_value = contract_size / pip_multiplier
            pnl = pip_diff * pip_value * trade['position_size']

            trade['outcome'] = pnl
            self.balance += pnl
            trade['balance_after'] = self.balance

            self.peak_balance = max(self.peak_balance, self.balance)
            drawdown = self.peak_balance - self.balance
            self.max_drawdown = max(self.max_drawdown, drawdown)

            logger.log(f"[PnL] Entry: {trade['entry_price']}, Exit: {exit_price}, Size: {trade['position_size']}, PnL: {pnl}")

    def generate_report(self):
        if not self.results:
            return pd.DataFrame(columns=[
                'entry_time', 'entry_price', 'position_size', 'exit_price', 'exit_time', 'outcome',
                'balance_before', 'balance_after', 'profit_loss', 'max_drawdown', 'starting_balance', 'final_balance', 'total_return', 'total_trades'
            ])

        report = pd.DataFrame(self.results)
        report['profit_loss'] = report['outcome'].cumsum()
        report['max_drawdown'] = self.max_drawdown
        report['starting_balance'] = self.starting_balance
        report['final_balance'] = self.balance
        report['total_return'] = self.balance - self.starting_balance
        report['total_trades'] = len(report)

        logger.log(f"📈 Starting Balance: {self.starting_balance}")
        logger.log(f"📈 Final Balance: {self.balance}")
        logger.log(f"📉 Max Drawdown: {self.max_drawdown}")
        logger.log(f"📊 Total Return: {self.balance - self.starting_balance}")
        logger.log(f"📄 Total Trades: {len(report)}")

        return report

    def _plot_equity_curve(self):
        plt.figure(figsize=(10, 4))
        plt.plot(self.equity_curve, label="Equity Curve")
        plt.title("Equity Curve")
        plt.xlabel("Time Step")
        plt.ylabel("Account Balance")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def evaluate_performance(self):
        total_profit = sum(trade['outcome'] for trade in self.results if trade['outcome'] is not None)
        return total_profit / len(self.results) if self.results else 0.0


def fetch_mt5_data(symbol, timeframe, start_date, end_date):
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
