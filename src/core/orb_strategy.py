import pandas as pd
from datetime import time as dt_time

class OpeningRangeBreakout:
    def should_exit(self, row, entry_price, stop_loss, take_profit, position):
        """
        Determines if the strategy should exit a position based on the current row.

        Args:
            row (pd.Series): Current OHLCV market data.
            entry_price (float): Entry price of the position.
            stop_loss (float): Stop loss level.
            take_profit (float): Take profit level.
            position (str): 'buy' or 'sell'.

        Returns:
            bool: True if exit conditions are met, False otherwise.
        """

        price = row.get('Close') or row.get('close')
        if price is None or entry_price is None or stop_loss is None or take_profit is None or position not in ['buy', 'sell']:
            return False

        # 1. Exit on Stop Loss or Take Profit
        if position == 'buy':
            if price <= stop_loss:
                return True  # Stop loss hit
            if price >= take_profit:
                return True  # Take profit hit
            if self.or_high is not None and price < self.or_high:
                return True  # Returned inside the range
        elif position == 'sell':
            if price >= stop_loss:
                return True
            if price <= take_profit:
                return True
            if self.or_low is not None and price > self.or_low:
                return True

        # 2. Time-based exit (after ORB session)
        time_val = row.get('Time') or row.get('time')
        if time_val is not None:
            if isinstance(time_val, pd.Timestamp):
                time_val = time_val.time()
            elif isinstance(time_val, str):
                try:
                    parsed = pd.to_datetime(time_val)
                    time_val = parsed.time()
                except Exception:
                    pass
            elif hasattr(time_val, 'hour') and hasattr(time_val, 'minute') and not isinstance(time_val, dt_time):
                time_val = dt_time(time_val.hour, time_val.minute)

            ed_dt = pd.to_datetime(self.end_time)
            if isinstance(time_val, dt_time) and time_val > ed_dt.time():
                return True  # Exit after session

        return False

    
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time
        self.or_high = None
        self.or_low = None

    def define_opening_range(self, ohlcv_data):
        """Define the opening range based on the first 30 minutes of trading."""
        opening_candle = ohlcv_data.between_time(self.start_time, self.end_time).iloc[0]
        self.or_high = opening_candle['high']
        self.or_low = opening_candle['low']

    def monitor_breakout(self, current_price):
        """Check for breakout conditions."""
        if current_price > self.or_high:
            return 'buy'
        elif current_price < self.or_low:
            return 'sell'
        return None

    def reset(self):
        """Reset the opening range values."""
        self.or_high = None
        self.or_low = None

    def get_opening_range(self):
        """Return the current opening range high and low."""
        return self.or_high, self.or_low

    def is_setup_valid(self, row, s_r_levels, patterns):
        """
        Validates if the current setup meets the ORB strategy requirements.
        Args:
            row: Current market data row (OHLCV or dict-like)
            s_r_levels: Support/Resistance levels (list or dict)
            patterns: List of detected patterns
        Returns:
            bool: True if setup is valid, False otherwise
        """
        # 1. Confirm price is near a support or resistance zone
        price = row['close'] if 'close' in row else row.get('Close', None)
        if price is None:
            return False
        sr_near = False
        sr_threshold = 0.001 * price  # 0.1% proximity
        if isinstance(s_r_levels, dict):
            sr_values = list(s_r_levels.values())
        else:
            sr_values = s_r_levels
        for sr in sr_values:
            if abs(price - sr) <= sr_threshold:
                sr_near = True
                break
        if not sr_near:
            return False

        # 2. Confirm within ORB window (time check)
        if 'time' in row:
            time_val = row['time']
        elif 'Time' in row:
            time_val = row['Time']
        else:
            time_val = None
        if time_val is not None:
            import pandas as pd
            from datetime import time as dt_time
            # Convert time_val to datetime.time if needed
            if isinstance(time_val, pd.Timestamp):
                time_val = time_val.time()
            elif isinstance(time_val, str):
                try:
                    parsed = pd.to_datetime(time_val)
                    time_val = parsed.time() if hasattr(parsed, 'time') else time_val
                except Exception:
                    h, m = map(int, time_val.split(':'))
                    time_val = dt_time(h, m)
            elif hasattr(time_val, 'hour') and hasattr(time_val, 'minute') and not isinstance(time_val, dt_time):
                time_val = dt_time(time_val.hour, time_val.minute)
            # Now compare
            if hasattr(self, 'start_time') and hasattr(self, 'end_time'):
                st_dt = pd.to_datetime(self.start_time)
                ed_dt = pd.to_datetime(self.end_time)
                st_time = st_dt.time()
                ed_time = ed_dt.time()

                if not (st_time <= time_val <= ed_time):
                    return False

        # 3. Confirm a valid pattern is present
        valid_patterns = {
            "Bullish Engulfing", "Bearish Engulfing", "Morning Star", "Evening Star",
            "Piercing Line", "Dark Cloud Cover", "Double Top", "Double Bottom",
            "Ascending Triangle", "Descending Triangle", "Bull Flag", "Bear Flag"
        }
        pattern_found = any(p in valid_patterns for p in patterns)
        if not pattern_found:
            return False

        # 4. Confirm volume is above average (if available)
        if 'volume' in row:
            volume = row['volume']
        elif 'Volume' in row:
            volume = row['Volume']
        else:
            volume = None
        if volume is not None and 'avg_volume' in row:
            avg_volume = row['avg_volume']
            if volume < avg_volume:
                return False

        # 5. Optional: Confirm pattern strength if provided
        if 'pattern_strength' in row:
            if row['pattern_strength'] < 0.7:
                return False

        return True