import MetaTrader5 as mt5
import time

class Trader:
    def __init__(self, config):
        self.config = config

    def connect(self):
        if not mt5.initialize():
            print("Failed to initialize MT5 connection")
            return False
        print("Connected to MT5")
        return True

    def send_order(self, symbol, order_type, volume, sl, tp):
        order = {
            'symbol': symbol,
            'action': order_type,
            'volume': volume,
            'sl': sl,
            'tp': tp
        }
        result = mt5.order_send(order)
        if result.retcode != 0:
            print(f"Order failed: {result.comment}")
        else:
            print(f"Order sent: {order}")

    def modify_position(self, ticket, sl, tp):
        result = mt5.order_modify(ticket, sl, tp)
        if result.retcode != 0:
            print(f"Failed to modify position: {result.comment}")
        else:
            print(f"Position modified: Ticket {ticket}")

    def close_position(self, ticket):
        result = mt5.order_close(ticket)
        if result.retcode != 0:
            print(f"Failed to close position: {result.comment}")
        else:
            print(f"Position closed: Ticket {ticket}")

    def monitor_trades(self):
        while True:
            positions = mt5.positions_get()
            for position in positions:
                print(f"Monitoring position: {position}")
            time.sleep(60)  # Check every minute

    def disconnect(self):
        mt5.shutdown()
        print("Disconnected from MT5")