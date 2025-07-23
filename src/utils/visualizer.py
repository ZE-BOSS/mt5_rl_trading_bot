from matplotlib import pyplot as plt
import pandas as pd

def plot_trade_results(trade_data):
    """
    Plots the results of trades over time.

    Parameters:
    trade_data (pd.DataFrame): DataFrame containing trade results with columns ['date', 'profit', 'equity'].
    """
    plt.figure(figsize=(12, 6))
    plt.plot(trade_data['date'], trade_data['equity'], label='Equity', color='blue')
    plt.plot(trade_data['date'], trade_data['profit'].cumsum(), label='Cumulative Profit', color='green')
    plt.title('Trade Results Over Time')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.legend()
    plt.grid()
    plt.show()

def visualize_patterns(pattern_data):
    """
    Visualizes detected candlestick patterns on a price chart.

    Parameters:
    pattern_data (pd.DataFrame): DataFrame containing price data with columns ['date', 'open', 'high', 'low', 'close'].
    """
    plt.figure(figsize=(12, 6))
    plt.plot(pattern_data['date'], pattern_data['close'], label='Close Price', color='black')
    plt.title('Price Chart with Detected Patterns')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid()
    plt.show()

def save_chart_as_image(filename):
    """
    Saves the current chart as an image file.

    Parameters:
    filename (str): The name of the file to save the chart as.
    """
    plt.savefig(filename)

def plot_support_resistance(support_levels, resistance_levels, price_data):
    """
    Plots support and resistance levels on the price chart.

    Parameters:
    support_levels (list): List of support levels.
    resistance_levels (list): List of resistance levels.
    price_data (pd.DataFrame): DataFrame containing price data with columns ['date', 'close'].
    """
    plt.figure(figsize=(12, 6))
    plt.plot(price_data['date'], price_data['close'], label='Close Price', color='black')
    for level in support_levels:
        plt.axhline(y=level, color='red', linestyle='--', label='Support Level' if level == support_levels[0] else "")
    for level in resistance_levels:
        plt.axhline(y=level, color='green', linestyle='--', label='Resistance Level' if level == resistance_levels[0] else "")
    plt.title('Price Chart with Support and Resistance Levels')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid()
    plt.show()