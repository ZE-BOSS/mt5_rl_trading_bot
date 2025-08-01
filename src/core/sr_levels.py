import MetaTrader5 as mt5
import numpy as np
import pandas as pd

class SupportResistance:
    def __init__(self, symbol, timeframe, num_levels=5, window=20):
        self.symbol = symbol
        self.timeframe = timeframe
        self.num_levels = num_levels
        self.sr_levels = []
        self.window = window
        self.history = []

    def fetch_historical_data(self, start_date, end_date):
        rates = mt5.copy_rates_range(self.symbol, self.timeframe, start_date, end_date)
        return pd.DataFrame(rates)

    def calculate_sr_levels(self, historical_data):
        highs = historical_data['high']
        lows = historical_data['low']
        
        # Calculate support and resistance levels
        self.sr_levels = self.detect_levels(highs, lows)

    def detect_levels(self, highs, lows):
        levels = []
        # Identify support and resistance levels based on swing highs/lows
        for i in range(len(highs) - 1):
            if highs[i] > highs[i + 1] and highs[i] > highs[i - 1]:
                levels.append(highs[i])
            if lows[i] < lows[i + 1] and lows[i] < lows[i - 1]:
                levels.append(lows[i])
        
        # Remove duplicates and sort levels
        levels = sorted(set(levels), reverse=True)
        return levels[:self.num_levels]

    def update_sr_levels(self):
        # Fetch recent historical data
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(months=1)
        historical_data = self.fetch_historical_data(start_date, end_date)
        
        # Calculate new support and resistance levels
        self.calculate_sr_levels(historical_data)

    def get_sr_levels(self, row):
        # Add the current row to history
        self.history.append(row)
        # Keep only the last 'window' rows
        if len(self.history) > self.window:
            self.history.pop(0)
        # Convert to DataFrame for calculation
        import pandas as pd
        df = pd.DataFrame(self.history)
        # Calculate support (lowest low) and resistance (highest high) in the window
        support = df['Low'].min() if not df.empty else row['Low']
        resistance = df['High'].max() if not df.empty else row['High']
        # Optionally, add more advanced logic here
        sr_levels = {'support': support, 'resistance': resistance}
        
        return sr_levels