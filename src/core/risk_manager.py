from typing import Dict
from src.utils.logger import Logger

logger = Logger('backtest_reports/trading_bot.log')

class RiskManager:
    def __init__(self, account_balance: float, risk_per_trade: float):
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade

    def calculate_lot_size(self, entry_signal, symbol):
        if not entry_signal or 'stop_loss' not in entry_signal or 'price' not in entry_signal:
            return 0

        try:
            entry_price = float(entry_signal["price"])
            stop_loss = float(entry_signal["stop_loss"])

            pip_multiplier, contract_size = self._get_multiplier_and_contract(symbol)

            stop_loss_pips = abs(entry_price - stop_loss) * pip_multiplier
            if stop_loss_pips == 0:
                return 0

            risk_amount = self.account_balance * self.risk_per_trade
            lot_size = risk_amount / (stop_loss_pips * (contract_size / pip_multiplier))

            # Enforce broker minimum (e.g., 0.01)
            lot_size = max(0.01, round(lot_size, 2))
            return lot_size

        except Exception as e:
            return 0

    def calculate_stop_loss(self, entry_price: float, direction: str, stop_loss_pips: float, symbol: str) -> float:
        pip_value = self._get_pip_value(symbol)
        if direction == 'buy':
            return entry_price - stop_loss_pips * pip_value
        elif direction == 'sell':
            return entry_price + stop_loss_pips * pip_value
        else:
            raise ValueError("Direction must be 'buy' or 'sell'.")

    def calculate_take_profit(self, entry_price: float, direction: str, take_profit_pips: float, symbol: str) -> float:
        pip_value = self._get_pip_value(symbol)
        if direction == 'buy':
            return entry_price + take_profit_pips * pip_value
        elif direction == 'sell':
            return entry_price - take_profit_pips * pip_value
        else:
            raise ValueError("Direction must be 'buy' or 'sell'.")

    def _get_pip_value(self, symbol: str) -> float:
        """
        Returns the pip size for the given symbol.
        You can extend this mapping for your broker's instrument list.
        """
        pip_map = {
            "EURUSDm": 0.0001,
            "GBPJPYm": 0.01,
            "XAUUSDm": 0.10,
            "XAGUSDm": 0.01,
            "US30": 1.0,
            "NAS100": 1.0,
            "BTCUSDm": 1.0,
            "ETHUSDm": 1.0,
            "USDJPYm": 0.01,
        }

        return pip_map.get(symbol.upper(), 0.0001)  # Default fallback for 0.0001

    def _get_multiplier_and_contract(self, symbol: str) -> (float, float):
        """
        Returns (pip_multiplier, contract_size) for symbol.
        These values are used to determine lot size and PnL.
        """
        symbol = symbol.upper()
        if symbol == "EURUSDm":
            return 10000, 100000
        elif symbol == "GBPJPYm":
            return 100, 100000
        elif symbol == "USDJPYm":
            return 100, 100000
        elif symbol == "XAUUSDm":
            return 10, 100
        elif symbol == "XAGUSDm":
            return 100, 5000
        elif symbol in {"US30", "NAS100", "BTCUSDm", "ETHUSDm"}:
            return 1, 1
        else:
            return 10000, 100000 

    def update_account_balance(self, profit_loss: float):
        self.account_balance += profit_loss

    def get_risk_parameters(self) -> Dict[str, float]:
        return {
            'account_balance': self.account_balance,
            'risk_per_trade': self.risk_per_trade
        }
