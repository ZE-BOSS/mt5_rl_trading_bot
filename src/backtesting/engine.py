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
        # Enhanced trade frequency constraints
        self.min_trades_per_week = 3
        self.max_trades_per_week = 10
        self.trades_this_week = 0
        self.current_week = None

    def run_backtest(self):
        trade_count = 0
        weekly_stats = {}

        for index, row in self.historical_data.iterrows():
            row_week = row['Time'].isocalendar().week

            if self.current_week is None:
                self.current_week = row_week
                self.trades_this_week = 0

            if row_week != self.current_week:
                # Log weekly summary
                weekly_stats[self.current_week] = {
                    "trades": self.trades_this_week,
                    "within_target": self.min_trades_per_week <= self.trades_this_week <= self.max_trades_per_week,
                    "balance": self.balance
                }
                
                if self.trades_this_week < self.min_trades_per_week:
                    logger.log(f"⚠️ Agent took only {self.trades_this_week} trades in week {self.current_week}. Target: {self.min_trades_per_week}-{self.max_trades_per_week}")
                elif self.trades_this_week > self.max_trades_per_week:
                    logger.log(f"⚠️ Agent took {self.trades_this_week} trades in week {self.current_week}. Exceeded maximum of {self.max_trades_per_week}")
                else:
                    logger.log(f"✅ Week {self.current_week}: {self.trades_this_week} trades (within target range)")
                
                self.current_week = row_week
                self.trades_this_week = 0

            if self.balance <= 0:
                logger.log("❌ Account balance depleted or zero. Ending backtest early and resetting agent's rewards.")
                self.env.balance = 0  # Simulate real environment balance collapse
                self.agent.memory.buffer.clear()  # Clear experience memory for this episode
                self.equity_curve.append(self.balance)
                break

            # Apply weekly trade frequency constraints
            if self.trades_this_week >= self.max_trades_per_week:
                logger.log(f"⏸️ Maximum weekly trades ({self.max_trades_per_week}) reached for week {self.current_week}. Skipping...")
                self.equity_curve.append(self.balance)
                continue

            # Check if we need to be more aggressive (increase trade frequency)
            days_into_week = (row['Time'] - row['Time'].replace(hour=0, minute=0, second=0, microsecond=0)).days % 7
            should_be_aggressive = days_into_week >= 3 and self.trades_this_week < self.min_trades_per_week

            if not self.in_trade and self.strategy.should_enter(row):
                entry_price = row['Close']
                base_position_size = self.strategy.calculate_position_size(entry_price)
                
                # Adjust position size based on weekly trade frequency
                if should_be_aggressive:
                    position_size = base_position_size * 1.3  # 30% more aggressive
                    logger.log(f"🔥 Increasing aggression: {self.trades_this_week}/{self.min_trades_per_week} trades this week")
                else:
                    position_size = base_position_size
                
                self.execute_trade(entry_price, position_size, row)
                logger.log(f'Trade({index}) entered at: {entry_price}, with lot size: {position_size}')
                self.in_trade = True
                trade_count += 1
                self.trades_this_week += 1

            if self.in_trade:
                exit_signal = self.strategy.should_exit(row)
                if isinstance(exit_signal, dict):
                    exit_price = exit_signal.get("exit_price", row['Close'])
                    self.close_trade(exit_price, row)
                    logger.log(f'Trade exited at: {exit_price}')
                    self.in_trade = False

            self.equity_curve.append(self.balance)

        # Final weekly summary
        if self.current_week and self.current_week not in weekly_stats:
            weekly_stats[self.current_week] = {
                "trades": self.trades_this_week,
                "within_target": self.min_trades_per_week <= self.trades_this_week <= self.max_trades_per_week,
                "balance": self.balance
            }

        # Log overall weekly performance
        weeks_within_target = sum(1 for stats in weekly_stats.values() if stats["within_target"])
        total_weeks = len(weekly_stats)
        
        logger.log(f"📊 Weekly Performance Summary:")
        logger.log(f"   Total weeks: {total_weeks}")
        logger.log(f"   Weeks within target ({self.min_trades_per_week}-{self.max_trades_per_week} trades): {weeks_within_target}")
        logger.log(f"   Target achievement rate: {(weeks_within_target/total_weeks*100):.1f}%" if total_weeks > 0 else "   Target achievement rate: N/A")
        
        for week, stats in weekly_stats.items():
            status = "✅" if stats["within_target"] else "❌"
            logger.log(f"   Week {week}: {stats['trades']} trades {status}")

        if not self.results:
            logger.log("⚠️ No trades were executed or retained during this backtest.")

    def should_increase_trade_frequency(self, row):
        """Determine if we should be more aggressive in taking trades"""
        days_into_week = (row['Time'] - row['Time'].replace(hour=0, minute=0, second=0, microsecond=0)).days % 7
        return days_into_week >= 3 and self.trades_this_week < self.min_trades_per_week

    def should_decrease_trade_frequency(self):
        """Determine if we should be less aggressive in taking trades"""
        return self.trades_this_week >= self.max_trades_per_week

    def execute_trade(self, entry_price, position_size, row):
        trade = {
            'entry_time': row['Time'],
            'entry_price': entry_price,
            'position_size': position_size,
            'exit_price': None,
            'exit_time': None,
            'outcome': None,
            'balance_before': self.balance,
            'week': row['Time'].isocalendar().week,
            'trades_this_week_before': self.trades_this_week
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
                'balance_before', 'balance_after', 'profit_loss', 'max_drawdown', 'starting_balance', 
                'final_balance', 'total_return', 'total_trades', 'week', 'trades_this_week_before'
            ])

        report = pd.DataFrame(self.results)
        report['profit_loss'] = report['outcome'].cumsum()
        report['max_drawdown'] = self.max_drawdown
        report['starting_balance'] = self.starting_balance
        report['final_balance'] = self.balance
        report['total_return'] = self.balance - self.starting_balance
        report['total_trades'] = len(report)

        # Add weekly analysis
        weekly_summary = report.groupby('week').agg({
            'outcome': ['count', 'sum'],
            'trades_this_week_before': 'first'
        }).round(2)
        
        logger.log(f"📈 Starting Balance: {self.starting_balance}")
        logger.log(f"📈 Final Balance: {self.balance}")
        logger.log(f"📉 Max Drawdown: {self.max_drawdown}")
        logger.log(f"📊 Total Return: {self.balance - self.starting_balance}")
        logger.log(f"📄 Total Trades: {len(report)}")
        
        return report

    def _plot_equity_curve(self):
        plt.figure(figsize=(12, 8))
        
        # Main equity curve
        plt.subplot(2, 1, 1)
        plt.plot(self.equity_curve, label="Equity Curve", linewidth=2)
        plt.title("Enhanced Equity Curve with Trade Frequency Analysis")
        plt.xlabel("Time Step")
        plt.ylabel("Account Balance")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Weekly trade frequency
        plt.subplot(2, 1, 2)
        if self.results:
            weekly_trades = pd.DataFrame(self.results).groupby('week')['outcome'].count()
            weeks = weekly_trades.index
            trades_per_week = weekly_trades.values
            
            colors = ['red' if t < self.min_trades_per_week or t > self.max_trades_per_week else 'green' for t in trades_per_week]
            plt.bar(weeks, trades_per_week, color=colors, alpha=0.7)
            plt.axhline(y=self.min_trades_per_week, color='orange', linestyle='--', label=f'Min Trades ({self.min_trades_per_week})')
            plt.axhline(y=self.max_trades_per_week, color='red', linestyle='--', label=f'Max Trades ({self.max_trades_per_week})')
            plt.title("Weekly Trade Frequency")
            plt.xlabel("Week")
            plt.ylabel("Number of Trades")
            plt.legend()
            plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()

    def evaluate_performance(self):
        total_profit = sum(trade['outcome'] for trade in self.results if trade['outcome'] is not None)
        return total_profit / len(self.results) if self.results else 0.0
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
