import pandas as pd
from datetime import time
from src.utils.logger import Logger

class OpeningRangeBreakout:
    def __init__(self, start_time="07:00", end_time="07:30", logger=None):
        self.start_time = pd.to_datetime(start_time).time()
        self.end_time = pd.to_datetime(end_time).time()
        self.or_high = None
        self.or_low = None
        self.logger = Logger('backtest_reports/trading_bot.log')

    def is_setup_valid(self, row, s_r_levels, patterns):
        row_time = row['Time'].time()
        # self.logger.log(f"[ORB] Checking setup validity for time: {row_time}")

        # Time check
        if not (self.start_time <= row_time <= self.end_time):
            # self.logger.log(f"[ORB] Time {row_time} outside of entry window: {self.start_time} - {self.end_time}")
            return False

        # Support/resistance proximity check
        price = row['Close']
        sr_threshold = 0.001 * price
        near_support = any(abs(price - level) < sr_threshold for level in s_r_levels.values())
        # self.logger.log(f"[ORB] Price: {price} | SR threshold: {sr_threshold} | Near support: {near_support}")
        if not near_support:
            # self.logger.log("[ORB] Price not near any SR level, setup invalid.")
            return False

        # Candlestick pattern check
        required_patterns = {
            "Bullish Engulfing", "Bearish Engulfing",
            "Morning Star", "Evening Star",
            "Hammer", "Hanging Man",
            "Doji", "Inverted Hammer",
            "Shooting Star", "Piercing Line",
            "Dark Cloud Cover", "Three White Soldiers",
            "Three Black Crows", "Harami", "Marubozu"
        }

        matched_patterns = [p for p in patterns if p in required_patterns]
        # self.logger.log(f"[ORB] Patterns detected: {patterns}")
        # self.logger.log(f"[ORB] Matched patterns: {matched_patterns}")

        if not matched_patterns:
            # self.logger.log("[ORB] No required pattern matched, setup invalid.")
            return False

        # self.logger.log("[ORB] Setup is valid.")
        return True

    def get_entry_signal(self, row):
        price = row['Close']
        symbol = row.get('symbol', 'symbol')  # Assumes symbol is included in row

        # Set OR high/low if not already set
        if self.or_high is None or self.or_low is None:
            self.or_high = row['High']
            self.or_low = row['Low']
            # self.logger.log(f"[ORB] Initial OR range set: High={self.or_high}, Low={self.or_low}")

        # self.logger.log(f"[ORB] Checking entry signal at price: {price}")

        if price > self.or_high:
            # self.logger.log(f"[ORB] Price {price} > OR High {self.or_high}. Signal: BUY")
            return {
                'symbol': symbol,
                'direction': 'buy',
                'price': price,
                'stop_loss': self.or_low,
                'take_profit': price + (100 * 0.0001)
            }
        elif price < self.or_low:
            # self.logger.log(f"[ORB] Price {price} < OR Low {self.or_low}. Signal: SELL")
            return {
                'symbol': symbol,
                'direction': 'sell',
                'price': price,
                'stop_loss': self.or_high,
                'take_profit': price - (100 * 0.0001)
            }

        # self.logger.log("[ORB] No breakout occurred, no signal generated.")
        return None
    
    def get_exit_signal(self, row, s_r_levels, patterns):
        """
        Determines whether an exit signal should be triggered based on:
        - Hitting support/resistance
        - Detected reversal patterns
        - Breach of ORB range in reverse
        - Time-based expiry
        - Stop loss or take profit breach
        """
        time = row['Time']
        close = row['Close']
        high = row['High']
        low = row['Low']

        if not hasattr(self, 'current_trade') or self.current_trade not in {"long", "short"}:
            return None

        # === 1. S/R Level Check ===
        if self.current_trade == "long" and close >= s_r_levels.get("resistance", float('inf')):
            return {
                "reason": "Price reached resistance",
                "exit_price": close,
                "time": time
            }

        if self.current_trade == "short" and close <= s_r_levels.get("support", float('-inf')):
            return {
                "reason": "Price reached support",
                "exit_price": close,
                "time": time
            }

        # === 2. Reversal Candlestick Pattern Check ===
        reversal_patterns = {
            "long": {"Shooting Star", "Bearish Engulfing", "Evening Star", "Hanging Man", "Dark Cloud Cover"},
            "short": {"Hammer", "Bullish Engulfing", "Morning Star", "Inverted Hammer", "Piercing Line"},
        }

        matched_reversals = [p for p in patterns if p in reversal_patterns.get(self.current_trade, set())]
        if matched_reversals:
            return {
                "reason": "Reversal candlestick pattern",
                "exit_price": close,
                "pattern_match": matched_reversals,
                "time": time
            }

        # === 3. Chart Pattern Check ===
        if self.current_trade == "long" and "Double Top" in patterns:
            return {
                "reason": "Double Top reversal",
                "exit_price": close,
                "time": time
            }

        if self.current_trade == "short" and "Double Bottom" in patterns:
            return {
                "reason": "Double Bottom reversal",
                "exit_price": close,
                "time": time
            }

        # === 4. ORB Breach Reversal ===
        orb_high = getattr(self, "orb_high", None)
        orb_low = getattr(self, "orb_low", None)

        if self.current_trade == "long" and orb_low is not None and close < orb_low:
            return {
                "reason": "Price breached ORB low in long trade",
                "exit_price": close,
                "time": time
            }

        if self.current_trade == "short" and orb_high is not None and close > orb_high:
            return {
                "reason": "Price breached ORB high in short trade",
                "exit_price": close,
                "time": time
            }

        # === 5. Time-Based Exit ===
        if hasattr(self, "entry_time"):
            exit_hold_minutes = 60 * 24  # 1 day
            elapsed_minutes = (time - self.entry_time).total_seconds() / 60
            if elapsed_minutes > exit_hold_minutes:
                return {
                    "reason": "Time-based exit",
                    "exit_price": close,
                    "time": time
                }

        # === 6. Stop Loss and Take Profit Logic ===
        entry_price = getattr(self, "entry_price", None)
        stop_loss_price = getattr(self, "stop_loss_price", None)
        take_profit_price = getattr(self, "take_profit_price", None)

        if entry_price is not None and stop_loss_price is not None:
            if self.current_trade == "long" and close <= stop_loss_price:
                return {
                    "reason": "Hit stop loss (long)",
                    "exit_price": close,
                    "time": time
                }
            elif self.current_trade == "short" and close >= stop_loss_price:
                return {
                    "reason": "Hit stop loss (short)",
                    "exit_price": close,
                    "time": time
                }

        if entry_price is not None and take_profit_price is not None:
            if self.current_trade == "long" and close >= take_profit_price:
                return {
                    "reason": "Hit take profit (long)",
                    "exit_price": close,
                    "time": time
                }
            elif self.current_trade == "short" and close <= take_profit_price:
                return {
                    "reason": "Hit take profit (short)",
                    "exit_price": close,
                    "time": time
                }

        return None

