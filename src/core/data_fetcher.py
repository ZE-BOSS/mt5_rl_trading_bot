import MetaTrader5 as mt5
import pandas as pd
import datetime

class DataFetcher:
    def __init__(self, symbol, timeframe, start_date, end_date):
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.connected = self.connect_to_mt5()

    def connect_to_mt5(self):
        if not mt5.initialize():
            print("Failed to initialize MT5 connection")
            return False
        return True

    def fetch_historical_data(self):
        rates = mt5.copy_rates_range(self.symbol, self.timeframe, self.start_date, self.end_date)
        if rates is None:
            print(f"Failed to fetch historical data for {self.symbol}")
            return None
        return pd.DataFrame(rates)

    def fetch_live_data(self):
        live_data = mt5.symbol_info_tick(self.symbol)
        if live_data is None:
            print(f"Failed to fetch live data for {self.symbol}")
            return None
        return live_data

    def fetch_account_details(self):
        account_info = mt5.account_info()
        if account_info is None:
            print("Failed to fetch account details")
            return None
        return account_info

    def disconnect(self):
        mt5.shutdown()