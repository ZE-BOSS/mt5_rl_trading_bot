from typing import Dict

class RiskManager:
    def __init__(self, account_balance: float, risk_per_trade: float):
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade

    def calculate_lot_size(self, stop_loss_pips: float) -> float:
        risk_amount = self.account_balance * (self.risk_per_trade / 100)
        lot_size = risk_amount / (stop_loss_pips * 10)  # Assuming 1 pip = 10 units for standard lot
        return lot_size

    def calculate_stop_loss(self, entry_price: float, direction: str, stop_loss_pips: float) -> float:
        if direction == 'buy':
            return entry_price - stop_loss_pips * 0.0001  # Adjust for the currency pair
        elif direction == 'sell':
            return entry_price + stop_loss_pips * 0.0001  # Adjust for the currency pair
        else:
            raise ValueError("Direction must be 'buy' or 'sell'.")

    def calculate_take_profit(self, entry_price: float, direction: str, take_profit_pips: float) -> float:
        if direction == 'buy':
            return entry_price + take_profit_pips * 0.0001  # Adjust for the currency pair
        elif direction == 'sell':
            return entry_price - take_profit_pips * 0.0001  # Adjust for the currency pair
        else:
            raise ValueError("Direction must be 'buy' or 'sell'.")

    def update_account_balance(self, profit_loss: float):
        self.account_balance += profit_loss

    def get_risk_parameters(self) -> Dict[str, float]:
        return {
            'account_balance': self.account_balance,
            'risk_per_trade': self.risk_per_trade
        }