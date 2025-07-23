import unittest
from src.backtesting.engine import BacktestEngine
from src.core.data_fetcher import DataFetcher

class TestBacktestEngine(unittest.TestCase):

    def setUp(self):
        self.data_fetcher = DataFetcher()
        self.backtest_engine = BacktestEngine()

    def test_backtest_initialization(self):
        self.backtest_engine.initialize('EURUSD', '2023-01-01', '2023-12-31')
        self.assertEqual(self.backtest_engine.symbol, 'EURUSD')
        self.assertEqual(self.backtest_engine.start_date, '2023-01-01')
        self.assertEqual(self.backtest_engine.end_date, '2023-12-31')

    def test_run_backtest(self):
        self.backtest_engine.initialize('EURUSD', '2023-01-01', '2023-12-31')
        results = self.backtest_engine.run()
        self.assertIsNotNone(results)
        self.assertIn('total_return', results)
        self.assertIn('max_drawdown', results)

    def test_data_fetching(self):
        historical_data = self.data_fetcher.get_historical_data('EURUSD', '2023-01-01', '2023-12-31')
        self.assertGreater(len(historical_data), 0)
        self.assertIn('open', historical_data.columns)
        self.assertIn('close', historical_data.columns)

if __name__ == '__main__':
    unittest.main()