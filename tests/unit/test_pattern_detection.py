import unittest
from src.core.pattern_detector import PatternDetector

class TestPatternDetection(unittest.TestCase):

    def setUp(self):
        self.detector = PatternDetector()

    def test_bullish_engulfing(self):
        # Sample data for bullish engulfing pattern
        candles = [
            {'open': 1.1000, 'close': 1.1050, 'high': 1.1060, 'low': 1.0990},
            {'open': 1.1040, 'close': 1.1080, 'high': 1.1090, 'low': 1.1030}
        ]
        result = self.detector.detect_bullish_engulfing(candles)
        self.assertTrue(result)

    def test_bearish_engulfing(self):
        # Sample data for bearish engulfing pattern
        candles = [
            {'open': 1.1050, 'close': 1.1000, 'high': 1.1060, 'low': 1.0990},
            {'open': 1.1010, 'close': 1.0950, 'high': 1.1020, 'low': 1.0940}
        ]
        result = self.detector.detect_bearish_engulfing(candles)
        self.assertTrue(result)

    def test_hammer(self):
        # Sample data for hammer pattern
        candles = [
            {'open': 1.1000, 'close': 1.1020, 'high': 1.1050, 'low': 1.0950}
        ]
        result = self.detector.detect_hammer(candles)
        self.assertTrue(result)

    def test_hanging_man(self):
        # Sample data for hanging man pattern
        candles = [
            {'open': 1.1050, 'close': 1.1020, 'high': 1.1060, 'low': 1.0950}
        ]
        result = self.detector.detect_hanging_man(candles)
        self.assertTrue(result)

    def test_double_top(self):
        # Sample data for double top pattern
        candles = [
            {'open': 1.1000, 'close': 1.1050, 'high': 1.1060, 'low': 1.0990},
            {'open': 1.1050, 'close': 1.1000, 'high': 1.1070, 'low': 1.0980},
            {'open': 1.1000, 'close': 1.0950, 'high': 1.1010, 'low': 1.0940}
        ]
        result = self.detector.detect_double_top(candles)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()