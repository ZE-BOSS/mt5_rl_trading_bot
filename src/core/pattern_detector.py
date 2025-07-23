from typing import List, Tuple
import numpy as np

class PatternDetector:
    def __init__(self):
        pass

    def detect_candlestick_patterns(self, data: List[Tuple]) -> List[str]:
        """
        Detects candlestick patterns in OHLCV data.
        Each tuple in data: (open, high, low, close, volume)
        """
        patterns = []
        for i in range(1, len(data)):
            o1, h1, l1, c1, v1 = data[i-1]
            o2, h2, l2, c2, v2 = data[i]

            # Bullish Engulfing
            if c1 < o1 and c2 > o2 and c2 > o1 and o2 < c1:
                patterns.append("Bullish Engulfing")
            # Bearish Engulfing
            if c1 > o1 and c2 < o2 and c2 < o1 and o2 > c1:
                patterns.append("Bearish Engulfing")
            # Hammer
            if (h2 - l2) > 3 * (o2 - c2) and (c2 - l2) / (0.001 + h2 - l2) > 0.6:
                patterns.append("Hammer")
            # Hanging Man
            if (h2 - l2) > 3 * (o2 - c2) and (o2 - l2) / (0.001 + h2 - l2) > 0.6:
                patterns.append("Hanging Man")
            # Morning Star
            if i > 1:
                o0, h0, l0, c0, v0 = data[i-2]
                if c0 < o0 and abs(c1 - o1) < 0.3 * (h1 - l1) and c2 > o2 and c2 > ((c0 + o0) / 2):
                    patterns.append("Morning Star")
            # Evening Star
            if i > 1:
                o0, h0, l0, c0, v0 = data[i-2]
                if c0 > o0 and abs(c1 - o1) < 0.3 * (h1 - l1) and c2 < o2 and c2 < ((c0 + o0) / 2):
                    patterns.append("Evening Star")
            # Piercing Line
            if c1 < o1 and c2 > o2 and o2 < c1 and c2 > (o1 + c1) / 2:
                patterns.append("Piercing Line")
            # Dark Cloud Cover
            if c1 > o1 and c2 < o2 and o2 > c1 and c2 < (o1 + c1) / 2:
                patterns.append("Dark Cloud Cover")
        return patterns

    def detect_chart_patterns(self, data: List[Tuple]) -> List[str]:
        """
        Detects chart patterns in OHLCV data.
        Each tuple in data: (open, high, low, close, volume)
        """
        patterns = []
        
        closes = np.array(data['Close'].astype(float))
        highs = np.array(data['High'].astype(float))
        lows = np.array(data['Low'].astype(float))

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
            lows_last = lows[-5:]
            if np.all(np.diff(lows_last) > 0) and np.allclose(highs[-5:], resistance, atol=0.001 * resistance):
                patterns.append("Ascending Triangle")
        # Descending Triangle
        if len(lows) >= 5:
            support = np.min(lows[-5:])
            highs_last = highs[-5:]
            if np.all(np.diff(highs_last) < 0) and np.allclose(lows[-5:], support, atol=0.001 * support):
                patterns.append("Descending Triangle")
        # Bull Flag
        if len(closes) >= 6:
            if closes[-6] < closes[-5] < closes[-4] and closes[-3] > closes[-4] and closes[-2] > closes[-3]:
                patterns.append("Bull Flag")
        # Bear Flag
        if len(closes) >= 6:
            if closes[-6] > closes[-5] > closes[-4] and closes[-3] < closes[-4] and closes[-2] < closes[-3]:
                patterns.append("Bear Flag")
        return patterns

    def analyze_patterns(self, data: List[Tuple]) -> List[str]:
        detected_patterns = self.detect_candlestick_patterns(data) + self.detect_chart_patterns(data)
        return detected_patterns

    def is_pattern_confirmed(self, pattern: str, context: dict) -> bool:
        """
        Confirms if a detected pattern aligns with the trading strategy:
        - Must align with S/R zones
        - Must occur during ORB window (if required)
        - Optionally, check volume and other confluence factors
        context example:
            {
                "sr_zone": True/False,
                "orb_window": True/False,
                "volume_confirmed": True/False,
                "pattern_strength": float,
            }
        """
        # Confirm S/R zone alignment
        if not context.get("sr_zone", False):
            return False
        # Confirm ORB window if required for strategy
        if pattern in [
            "Bullish Engulfing", "Bearish Engulfing", "Morning Star", "Evening Star",
            "Piercing Line", "Dark Cloud Cover"
        ] and not context.get("orb_window", False):
            return False
        # Confirm volume if required
        if context.get("volume_required", False) and not context.get("volume_confirmed", False):
            return False
        # Optionally, check pattern strength threshold
        if context.get("pattern_strength", 1.0) < 0.7:
            return False
        return True

# Example usage:
# detector = PatternDetector()
# patterns = detector.analyze_patterns(data)  # data should be OHLCV format
# confirmed_patterns = [p for p in patterns if detector.is_pattern_confirmed(p, context)]