import os
import time
import yaml
import pytz
import MetaTrader5 as mt5
from datetime import datetime
from src.utils.secrets_manager import SecretsManager
from src.core.data_fetcher import DataFetcher
from src.core.trader import Trader
from src.core.risk_manager import RiskManager
from src.core.orb_strategy import OpeningRangeBreakout
from src.reinforcement.agent import DQNAgent
from src.utils.logger import Logger
from src.utils.reporter import Reporter
from src.core.time_manager import TimeManager
from src.core.pattern_detector import PatternDetector
from src.integration.news_filter import NewsFilter
from src.integration.notifications import NotificationManager

class TradingBot:
    def __init__(self, config_path='config/bot_config.yaml'):
        self.sm = SecretsManager()
        self.load_config(config_path)
        self.logger = Logger()
        self.notifier = NotificationManager()
        self.reporter = Reporter()
        self.data_fetcher = DataFetcher(self.config['symbols'])
        self.trader = Trader(self.config)
        self.risk_manager = RiskManager(self.config['risk_parameters'])
        self.time_manager = TimeManager(self.config)
        self.orb_strategy = OpeningRangeBreakout()
        self.pattern_detector = PatternDetector()
        self.news_filter = NewsFilter(self.config['symbols'])
        self.rl_agent = self.init_rl_agent()
        self.open_positions = {}
        self.mt5_connected = False

    def load_config(self, config_path):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Override from .env
        self.config['mt5'] = {
            'login': os.getenv('MT5_LOGIN'),
            'password': self.sm.decrypt(os.getenv('MT5_PASSWORD')),
            'server': os.getenv('MT5_SERVER')
        }

    def init_rl_agent(self):
        if not os.getenv('REINFORCEMENT_LEARNING_ENABLED', 'True') == 'True':
            return None
            
        with open('config/rl_config.yaml', 'r') as file:
            rl_config = yaml.safe_load(file)
            
        return DQNAgent(
            state_size=self.config['rl_parameters']['state_size'],
            action_size=self.config['rl_parameters']['action_size'],
            config=rl_config
        )

    def connect_to_mt5(self):
        if not mt5.initialize(
            login=int(self.config['mt5']['login']),
            password=self.config['mt5']['password'],
            server=self.config['mt5']['server']
        ):
            self.logger.log_error("MT5 connection failed")
            return False
        self.mt5_connected = True
        return True

    def run(self):
        self.logger.log("Trading bot started")
        while True:
            current_time = datetime.now(pytz.utc)
            if self.time_manager.is_trading_time(current_time):
                try:
                    if not self.mt5_connected:
                        if not self.connect_to_mt5():
                            time.sleep(60)
                            continue
                    self.execute_trading_logic()
                except Exception as e:
                    self.logger.log_error(f"Trading error: {str(e)}")
                    self.notifier.send_error_alert(str(e))
            time.sleep(10)

    def execute_trading_logic(self):
        for symbol in self.config['symbols']:
            try:
                market_data = self.data_fetcher.fetch_ohlc_data(symbol, bars=100)
                if market_data is None or market_data.empty:
                    continue
                
                # Skip during news events
                if self.news_filter.is_high_impact_event(symbol):
                    self.logger.log(f"Skipping {symbol} during news event")
                    continue
                    
                # ORB Strategy
                s_r_levels = self.data_fetcher.get_sr_levels(symbol)
                patterns = self.pattern_detector.analyze_patterns(market_data)
                current_row = market_data.iloc[-1].to_dict()
                
                if self.orb_strategy.is_setup_valid(current_row, s_r_levels, patterns):
                    entry_signal = self.orb_strategy.get_entry_signal(current_row)
                    if entry_signal:
                        lot_size = self.risk_manager.calculate_position_size(
                            symbol, 
                            entry_signal['price'], 
                            entry_signal['stop_loss']
                        )
                        self.trader.execute_order(entry_signal, lot_size)
                        self.notifier.send_trade_alert(
                            symbol=entry_signal['symbol'],
                            action=entry_signal['direction'],
                            size=lot_size,
                            price=entry_signal['price'],
                            sl=entry_signal['stop_loss'],
                            tp=entry_signal.get('take_profit', 0)
                        )

                # RL Strategy
                if self.rl_agent:
                    state = self.prepare_rl_state(market_data)
                    action = self.rl_agent.act(state)
                    self.execute_rl_action(action, symbol)
                    
            except Exception as e:
                self.logger.log_error(f"Error processing {symbol}: {str(e)}")

    def prepare_rl_state(self, data):
        from src.utils.feature_engineering import add_technical_indicators
        processed = add_technical_indicators(data.copy())
        return processed.iloc[-1].values

    def execute_rl_action(self, action, symbol):
        if action == 0:  # Hold
            return
            
        direction = 'buy' if action < 4 else 'sell'
        sizes = [0, 0.1, 0.5, 1, 0.1, 0.5, 1]
        size = sizes[action]
        
        current_price = self.data_fetcher.fetch_live_price(symbol)
        stop_loss = self.risk_manager.calculate_stop_loss(
            current_price, 
            direction,
            stop_loss_pips=50,  # 50 pip SL
            symbol=symbol
        )
        
        take_profit = current_price + (100 * 0.0001) if direction == 'buy' else current_price - (100 * 0.0001)
        
        order = {
            'symbol': symbol,
            'direction': direction,
            'price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
        
        self.trader.execute_order(order, size)
        self.notifier.send_trade_alert(
            symbol=symbol,
            action=direction,
            size=size,
            price=current_price,
            sl=stop_loss,
            tp=take_profit
        )