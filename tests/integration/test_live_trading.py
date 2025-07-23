import unittest
from src.core.trader import Trader
from src.core.data_fetcher import DataFetcher
from src.core.risk_manager import RiskManager
from unittest.mock import patch

class TestLiveTrading(unittest.TestCase):

    @patch.object(DataFetcher, 'get_live_data')
    @patch.object(Trader, 'execute_order')
    @patch.object(RiskManager, 'calculate_position_size')
    def test_live_trading_execution(self, mock_calculate_position_size, mock_execute_order, mock_get_live_data):
        # Setup mock data
        mock_get_live_data.return_value = {
            'symbol': 'EURUSD',
            'bid': 1.1000,
            'ask': 1.1005,
            'volume': 1000
        }
        mock_calculate_position_size.return_value = 0.1

        trader = Trader()
        trader.execute_order('buy', 'EURUSD', 0.1, 1.1005)

        # Assertions
        mock_get_live_data.assert_called_once()
        mock_calculate_position_size.assert_called_once()
        mock_execute_order.assert_called_once_with('buy', 'EURUSD', 0.1, 1.1005)

    @patch.object(DataFetcher, 'get_account_details')
    def test_account_details_fetching(self, mock_get_account_details):
        # Setup mock account details
        mock_get_account_details.return_value = {
            'balance': 1000,
            'equity': 1000,
            'margin': 0
        }

        data_fetcher = DataFetcher()
        account_details = data_fetcher.get_account_details()

        # Assertions
        mock_get_account_details.assert_called_once()
        self.assertEqual(account_details['balance'], 1000)
        self.assertEqual(account_details['equity'], 1000)

if __name__ == '__main__':
    unittest.main()