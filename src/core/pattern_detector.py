from typing import List, Tuple
import numpy as np
import pandas as pd
from src.utils.logger import Logger

class PatternDetector:
    def __init__(self, logger=None):
        self.logger = Logger('backtest_reports/trading_bot.log')

    def detect_candlestick_patterns(self, data: pd.DataFrame) -> List[str]:
        patterns = []

        if len(data) < 3:
            # self.logger.log("Not enough data to detect candlestick patterns (need at least 3 rows).")
            return patterns

        # self.logger.log("Starting candlestick pattern detection.")

        for i in range(2, len(data)):
            row_time = data.iloc[i].get("Time", f"index {i}")
            o0, h0, l0, c0 = data.iloc[i - 2][['Open', 'High', 'Low', 'Close']]
            o1, h1, l1, c1 = data.iloc[i - 1][['Open', 'High', 'Low', 'Close']]
            o2, h2, l2, c2 = data.iloc[i][['Open', 'High', 'Low', 'Close']]

            body1 = abs(c1 - o1)
            body2 = abs(c2 - o2)
            total_range2 = h2 - l2

            # === Single Candle Patterns ===
            if total_range2 > 3 * body2 and (min(o2, c2) - l2) / (total_range2 + 1e-6) > 0.6:
                patterns.append("Hammer")

            if total_range2 > 3 * body2 and (o2 - l2) / (total_range2 + 1e-6) > 0.6:
                patterns.append("Hanging Man")

            if total_range2 > 3 * body2 and (h2 - max(o2, c2)) / (total_range2 + 1e-6) > 0.6:
                patterns.append("Inverted Hammer")

            if total_range2 > 3 * body2 and (h2 - max(o2, c2)) / (total_range2 + 1e-6) > 0.6 and c2 < o2:
                patterns.append("Shooting Star")

            if abs(h2 - c2) < 0.001 and abs(l2 - o2) < 0.001:
                patterns.append("Marubozu")

            if body2 / (total_range2 + 1e-6) < 0.1:
                patterns.append("Doji")

            # === Dual Candle Patterns ===
            if c1 < o1 and c2 > o2 and c2 > o1 and o2 < c1:
                patterns.append("Bullish Engulfing")

            if c1 > o1 and c2 < o2 and c2 < o1 and o2 > c1:
                patterns.append("Bearish Engulfing")

            if c1 < o1 and c2 > o2 and o2 < c1 and c2 > (o1 + c1) / 2:
                patterns.append("Piercing Line")

            if c1 > o1 and c2 < o2 and o2 > c1 and c2 < (o1 + c1) / 2:
                patterns.append("Dark Cloud Cover")

            if c1 < o1 and o2 < c2 and o2 > c1 and c2 < o1:
                patterns.append("Bullish Harami")

            if c1 > o1 and o2 > c2 and o2 < c1 and c2 > o1:
                patterns.append("Bearish Harami")

            # === Triple Candle Patterns ===
            if c0 < o0 and abs(c1 - o1) < 0.3 * (h1 - l1) and c2 > o2 and c2 > ((c0 + o0) / 2):
                patterns.append("Morning Star")

            if c0 > o0 and abs(c1 - o1) < 0.3 * (h1 - l1) and c2 < o2 and c2 < ((c0 + o0) / 2):
                patterns.append("Evening Star")

            if c0 < o0 and c1 > o1 and c2 > o2 and c2 > c1 > c0:
                patterns.append("Three White Soldiers")

            if c0 > o0 and c1 < o1 and c2 < o2 and c2 < c1 < c0:
                patterns.append("Three Black Crows")

            # if patterns:
                # self.logger.log(f"[{row_time}] Detected candlestick patterns: {patterns}")

        # if not patterns:
            # self.logger.log("No candlestick patterns detected.")
        return patterns


    def detect_chart_patterns(self, data: pd.DataFrame) -> List[str]:
        patterns = []

        if len(data) < 6:
            # self.logger.log("Not enough data to detect chart patterns (need at least 6 rows).")
            return patterns

        # self.logger.log("Starting chart pattern detection.")

        closes = data['Close'].astype(float).values
        highs = data['High'].astype(float).values
        lows = data['Low'].astype(float).values

        # Double Top
        if len(highs) >= 5:
            max1 = np.argmax(highs)
            highs_wo_max1 = np.delete(highs, max1)
            max2 = np.argmax(highs_wo_max1)
            if abs(highs[max1] - highs_wo_max1[max2]) < 0.002 * highs[max1]:
                patterns.append("Double Top")

        # Double Bottom
        if len(lows) >= 5:
            min1 = np.argmin(lows)
            lows_wo_min1 = np.delete(lows, min1)
            min2 = np.argmin(lows_wo_min1)
            if abs(lows[min1] - lows_wo_min1[min2]) < 0.002 * lows[min1]:
                patterns.append("Double Bottom")

        # Ascending Triangle
        if len(highs) >= 5:
            resistance = np.max(highs[-5:])
            if np.all(np.diff(lows[-5:]) > 0) and np.allclose(highs[-5:], resistance, atol=0.001 * resistance):
                patterns.append("Ascending Triangle")

        # Descending Triangle
        if len(lows) >= 5:
            support = np.min(lows[-5:])
            if np.all(np.diff(highs[-5:]) < 0) and np.allclose(lows[-5:], support, atol=0.001 * support):
                patterns.append("Descending Triangle")

        # Bull Flag
        if len(closes) >= 6:
            if closes[-6] < closes[-5] < closes[-4] and closes[-3] > closes[-4] and closes[-2] > closes[-3]:
                patterns.append("Bull Flag")

        # Bear Flag
        if len(closes) >= 6:
            if closes[-6] > closes[-5] > closes[-4] and closes[-3] < closes[-4] and closes[-2] < closes[-3]:
                patterns.append("Bear Flag")

        # if patterns:
        #     self.logger.log(f"Detected chart patterns: {patterns}")
        # else:
            # self.logger.log("No chart patterns detected.")

        return patterns

    def analyze_patterns(self, data: pd.DataFrame) -> List[str]:
        # self.logger.log("Analyzing full pattern set.")
        return self.detect_candlestick_patterns(data) + self.detect_chart_patterns(data)

    def is_pattern_confirmed(self, pattern: str, context: dict) -> bool:
        if not context.get("sr_zone", False):
            return False
        if pattern in {
            "Bullish Engulfing", "Bearish Engulfing", "Morning Star", "Evening Star",
            "Piercing Line", "Dark Cloud Cover", "Harami", "Three White Soldiers", "Three Black Crows"
        } and not context.get("orb_window", False):
            return False
        if context.get("volume_required", False) and not context.get("volume_confirmed", False):
            return False
        if context.get("pattern_strength", 1.0) < 0.7:
            return False
        return True
