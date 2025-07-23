import MetaTrader5 as mt5
import yaml

def load_config():
    with open('config/bot_config.yaml', 'r') as file:
        return yaml.safe_load(file)

def withdraw_profit(amount):
    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to retrieve account information.")
        return

    if account_info.balance < amount:
        print("Insufficient balance for withdrawal.")
        return

    result = mt5.order_send({
        "action": mt5.TRADE_ACTION_DEPOSIT,
        "amount": amount,
        "symbol": "USD",
        "type": mt5.ORDER_BUY,
        "sl": 0,
        "tp": 0,
        "deviation": 10,
        "magic": 0,
        "comment": "Profit withdrawal",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    })

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Withdrawal failed: {result.retcode}")
    else:
        print(f"Successfully withdrew {amount}.")

if __name__ == "__main__":
    config = load_config()
    withdraw_amount = config.get('withdraw_amount', 100)  # Default withdrawal amount
    withdraw_profit(withdraw_amount)