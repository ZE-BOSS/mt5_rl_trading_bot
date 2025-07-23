import unittest
from src.core.risk_manager import RiskManager

class TestRiskManager(unittest.TestCase):

    def setUp(self):
        self.risk_manager = RiskManager(account_balance=1000, risk_percentage=0.02)

    def test_calculate_lot_size(self):
        # Test for a stop loss of 10 pips
        stop_loss_pips = 10
        lot_size = self.risk_manager.calculate_lot_size(stop_loss_pips)
        expected_lot_size = (self.risk_manager.account_balance * self.risk_manager.risk_percentage) / (stop_loss_pips * 10)  # Assuming 10 is the pip value
        self.assertAlmostEqual(lot_size, expected_lot_size, places=2)

    def test_stop_loss_calculation_long(self):
        entry_price = 1.1000
        stop_loss = self.risk_manager.calculate_stop_loss(entry_price, direction='long')
        self.assertEqual(stop_loss, entry_price - 0.0005)  # 5 pips below entry

    def test_stop_loss_calculation_short(self):
        entry_price = 1.1000
        stop_loss = self.risk_manager.calculate_stop_loss(entry_price, direction='short')
        self.assertEqual(stop_loss, entry_price + 0.0005)  # 5 pips above entry

    def test_take_profit_calculation(self):
        entry_price = 1.1000
        tp1 = self.risk_manager.calculate_take_profit(entry_price, tp_multiplier=1)
        tp2 = self.risk_manager.calculate_take_profit(entry_price, tp_multiplier=2)
        self.assertEqual(tp1, entry_price + 0.0010)  # TP1 = OR height (10 pips)
        self.assertEqual(tp2, entry_price + 0.0020)  # TP2 = Next significant S/R level (20 pips)

if __name__ == '__main__':
    unittest.main()