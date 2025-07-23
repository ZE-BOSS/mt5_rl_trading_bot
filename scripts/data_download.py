import MetaTrader5 as mt5
import pandas as pd
import yaml
import os
import datetime

def load_config():
    with open(os.path.join('config', 'bot_config.yaml'), 'r') as file:
        return yaml.safe_load(file)

def fetch_historical_data(symbol, timeframe, start_date, end_date):
    if not mt5.initialize():
        print("initialize() failed")
        mt5.shutdown()
        return None

    rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
    mt5.shutdown()

    if rates is None:
        print(f"Failed to fetch data for {symbol}")
        return None

    return pd.DataFrame(rates)

def save_data_to_csv(data, symbol):
    filename = f"data/historical/{symbol}_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
    data.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def main():
    config = load_config()
    symbols = config['symbols']
    timeframe = mt5.TIMEFRAME_H1  # Example: hourly data
    start_date = datetime.datetime(2022, 1, 1)
    end_date = datetime.datetime.now()

    for symbol in symbols:
        historical_data = fetch_historical_data(symbol, timeframe, start_date, end_date)
        if historical_data is not None:
            save_data_to_csv(historical_data, symbol)

if __name__ == "__main__":
    main()