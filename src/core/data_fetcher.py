import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.core.sr_levels import SupportResistance

class DataFetcher:
    def __init__(self, symbols):
        self.symbols = symbols
        self.sr_managers = {symbol: SupportResistance(symbol) for symbol in symbols}
        self.connected = False

    def connect(self, mt5_config):
        if not mt5.initialize(
            login=int(mt5_config['login']),
            password=mt5_config['password'],
            server=mt5_config['server']
        ):
            return False
        self.connected = True
        return True

    def fetch_ohlc_data(self, symbol, bars=100, timeframe=mt5.TIMEFRAME_M15):
        if not self.connected:
            return None
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None:
            return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def fetch_live_price(self, symbol):
        if not self.connected:
            return None
        tick = mt5.symbol_info_tick(symbol)
        return (tick.ask + tick.bid)/2

    def get_sr_levels(self, symbol):
        if symbol not in self.sr_managers:
            self.sr_managers[symbol] = SupportResistance(symbol)
        return self.sr_managers[symbol].get_current_levels()

    def disconnect(self):
        if self.connected:
            mt5.shutdown()
            self.connected = False