import datetime
import yaml
import src.core.data_fetcher as data_fetcher
import src.core.trader as trader
import src.core.risk_manager as risk_manager
import src.core.orb_strategy as orb_strategy
import src.reinforcement.agent as agent
import src.utils.logger as logger
import src.utils.reporter as reporter
import src.core.time_manager as time_manager

class TradingBot:
    def __init__(self, config_path):
        self.load_config(config_path)
        self.data_fetcher = data_fetcher.DataFetcher(
            self.config['symbols'],
            self.config.get('timeframe', None),
            self.config.get('start_date', None),
            self.config.get('end_date', None)
        )
        self.trader = trader.Trader(self.config)
        self.risk_manager = risk_manager.RiskManager(
            self.config['risk_parameters'],
            self.config.get('risk_per_trade', None)
        )
        self.orb_strategy = orb_strategy.OpeningRangeBreakout(
            self.config.get('orb_start_time', None),
            self.config.get('orb_end_time', None)
        )
        rl_params = self.config.get('rl_parameters', {})
        action_size = rl_params.get('action_size', 2)
        state_size = rl_params.get('state_size', 10)
        if not isinstance(action_size, int) or action_size < 1:
            action_size = 2
        if not isinstance(state_size, int) or state_size < 1:
            state_size = 10
        self.rl_agent = agent.QLearningAgent(
            action_size,
            state_size,
            rl_params
        )
        self.logger = logger.Logger()
        journal_dir = self.config.get('journal_dir', 'journals/')
        self.reporter = reporter.Reporter(journal_dir)
        schedule = self.config.get('schedule', {
            'trading_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            'start_time': '07:00',
            'end_time': '17:00',
            'orb_window': '07:00-07:30',
            'avoid_times': ['12:00-06:00', '12:00-13:30', 'Friday 12:00-23:59']
        })
        self.time_manager = time_manager.TimeManager(schedule)
        import src.core.pattern_detector as pattern_detector
        self.pattern_detector = pattern_detector.PatternDetector()

    def load_config(self, config_path):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

    def run(self):
        import time
        self.logger.log("Trading bot started.")
        while True:
            current_time = datetime.datetime.now()
            if self.time_manager.is_trading_time(current_time):
                try:
                    self.execute_trading_logic()
                except Exception as e:
                    self.logger.log(f"Error during trading logic: {e}")
            else:
                self.logger.log("Outside trading hours. Waiting...")
            time.sleep(10)  # Sleep to avoid busy waiting

    def execute_trading_logic(self):
        market_data = self.data_fetcher.fetch_live_data()
        s_r_levels = self.data_fetcher.fetch_support_resistance_levels()
        # Use pattern_detector for candlestick and chart patterns
        patterns = self.pattern_detector.analyze_patterns(market_data)
        self.logger.log(f"Detected patterns: {patterns}")

        if self.orb_strategy.is_setup_valid(market_data, s_r_levels, patterns):
            entry_signal = self.orb_strategy.get_entry_signal(market_data)
            lot_size = self.risk_manager.calculate_lot_size(entry_signal)
            self.trader.execute_order(entry_signal, lot_size)
            self.logger.log(f"Order executed: {entry_signal}, Lot size: {lot_size}")
        else:
            self.logger.log("No valid setup found.")

        self.rl_agent.learn_from_environment(market_data)
        self.logger.log("RL agent updated.")

if __name__ == "__main__":
    bot = TradingBot(config_path='config/bot_config.yaml')
    bot.run()